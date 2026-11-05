from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, BusinessRuleError, ForbiddenError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import PICKUP_TRANSITIONS, NotificationType, PickupStatus, UserRole, ZoneStatus
from app.models import PickupRequest, User
from app.repositories.customer_repository import AddressRepository, CustomerRepository
from app.repositories.pickup_repository import PickupRepository
from app.repositories.waste_category_repository import WasteCategoryRepository
from app.schemas.pickup_request import PickupCreate
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.validators import get_or_404

# statuses a human may set directly; the rest are driven by assignment / collection workflows
MANUAL_STATUSES = (PickupStatus.APPROVED, PickupStatus.REJECTED)
CANCELLABLE = (PickupStatus.PENDING, PickupStatus.APPROVED, PickupStatus.ASSIGNED, PickupStatus.SCHEDULED)


class PickupService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PickupRepository(db)
        self.customers = CustomerRepository(db)
        self.addresses = AddressRepository(db)
        self.categories = WasteCategoryRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    # ------------------------------------------------------------------ access
    def _customer_for(self, actor: User, customer_id: int | None):
        if actor.role == UserRole.CUSTOMER:
            customer = self.customers.get_by_user(actor.id)
            if not customer:
                raise BadRequestError("No customer profile is linked to this account")
            return customer
        if not customer_id:
            raise BadRequestError("customer_id is required when creating a request on behalf of a customer")
        return get_or_404(self.customers, customer_id, "Customer")

    def get(self, pickup_id: int, actor: User | None = None) -> PickupRequest:
        pickup = get_or_404(self.repo, pickup_id, "Pickup request")
        if actor and actor.role == UserRole.CUSTOMER:
            customer = self.customers.get_by_user(actor.id)
            if not customer or customer.id != pickup.customer_id:
                raise ForbiddenError("You can only access your own pickup requests")
        return pickup

    # ------------------------------------------------------------------ create
    def create(self, actor: User, data: PickupCreate, ip: str | None = None) -> PickupRequest:
        customer = self._customer_for(actor, data.customer_id)
        if customer.service_status != ZoneStatus.ACTIVE:
            raise BusinessRuleError("Customer service is not active - pickup requests cannot be created")
        address = get_or_404(self.addresses, data.address_id, "Address")
        if address.customer_id != customer.id:
            raise BadRequestError("Address does not belong to this customer")
        category = get_or_404(self.categories, data.waste_category_id, "Waste category")
        if not category.is_active:
            raise BusinessRuleError("This waste category is not currently accepted")

        with transaction(self.db):
            pickup = self.repo.add(
                PickupRequest(
                    request_no=self.repo.next_number("PR"),
                    customer_id=customer.id,
                    address_id=address.id,
                    zone_id=address.zone_id or customer.zone_id,
                    waste_category_id=category.id,
                    estimated_quantity_kg=data.estimated_quantity_kg,
                    preferred_date=data.preferred_date,
                    priority=data.priority,
                    notes=data.notes,
                    requested_by_id=actor.id,
                )
            )
            self.audit.log(actor, "PICKUP_CREATED", "pickup_request", pickup.id, {"request_no": pickup.request_no}, ip)
            self.notify.notify_management(
                NotificationType.NEW_PICKUP_REQUEST,
                "New pickup request",
                f"{pickup.request_no}: {pickup.estimated_quantity_kg} kg of {category.name} awaiting approval",
                "pickup_request",
                pickup.id,
            )
        return pickup

    def list(self, actor: User, params: PageParams, **filters):
        if actor.role == UserRole.CUSTOMER:
            customer = self.customers.get_by_user(actor.id)
            filters["customer_id"] = customer.id if customer else -1
        return paginate(self.db, self.repo.filtered(**filters), params)

    # ------------------------------------------------------------ status changes
    def change_status(self, actor: User, pickup_id: int, status: PickupStatus, reason: str | None) -> PickupRequest:
        pickup = self.get(pickup_id)
        if status not in MANUAL_STATUSES:
            raise BadRequestError("Only 'approved' or 'rejected' can be set manually; other statuses follow the workflow")
        if status not in PICKUP_TRANSITIONS[pickup.status]:
            raise BusinessRuleError(f"Cannot move a pickup from '{pickup.status.value}' to '{status.value}'")
        if status == PickupStatus.REJECTED and not reason:
            raise BadRequestError("A reason is required when rejecting a request")
        with transaction(self.db):
            old = pickup.status
            pickup.status = status
            pickup.status_reason = reason
            self.audit.log(actor, f"PICKUP_{status.value.upper()}", "pickup_request", pickup.id, {"from": old.value, "reason": reason})
            customer = self.customers.get(pickup.customer_id)
            if customer and customer.user_id:
                self.notify.notify(
                    NotificationType.PENDING_APPROVAL,
                    f"Pickup {status.value}",
                    f"Your request {pickup.request_no} was {status.value}." + (f" Reason: {reason}" if reason else ""),
                    user_id=customer.user_id,
                    entity_type="pickup_request",
                    entity_id=pickup.id,
                )
        return pickup

    def cancel(self, actor: User, pickup_id: int, reason: str) -> PickupRequest:
        from app.services.assignment_service import AssignmentService  # local import avoids a cycle

        pickup = self.get(pickup_id, actor)
        if pickup.status not in CANCELLABLE:
            raise BusinessRuleError(f"A pickup in status '{pickup.status.value}' cannot be cancelled")
        with transaction(self.db):
            AssignmentService(self.db).cancel_for_pickup(actor, pickup)  # frees driver / vehicle / workers
            old = pickup.status
            pickup.status = PickupStatus.CANCELLED
            pickup.status_reason = reason
            self.audit.log(actor, "PICKUP_CANCELLED", "pickup_request", pickup.id, {"from": old.value, "reason": reason})
        return pickup

    def delete(self, actor: User, pickup_id: int) -> None:
        pickup = self.get(pickup_id)
        if pickup.status not in (PickupStatus.CANCELLED, PickupStatus.REJECTED, PickupStatus.PENDING):
            raise BusinessRuleError("Only pending, cancelled or rejected requests can be deleted")
        with transaction(self.db):
            self.repo.soft_delete(pickup)
            self.audit.log(actor, "PICKUP_DELETED", "pickup_request", pickup.id)
