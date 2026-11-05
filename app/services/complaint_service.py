from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, BusinessRuleError, ForbiddenError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import ComplaintStatus, NotificationType, UserRole
from app.models import Complaint, User
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.pickup_repository import PickupRepository
from app.repositories.user_repository import UserRepository
from app.schemas.complaint import ComplaintAssign, ComplaintCreate
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.validators import get_or_404

S = ComplaintStatus
TRANSITIONS = {
    S.OPEN: {S.ASSIGNED, S.IN_PROGRESS, S.REJECTED},
    S.ASSIGNED: {S.IN_PROGRESS, S.RESOLVED, S.REJECTED},
    S.IN_PROGRESS: {S.RESOLVED, S.REJECTED},
    S.RESOLVED: {S.CLOSED, S.IN_PROGRESS},  # in progress = re-opened
    S.CLOSED: set(),
    S.REJECTED: set(),
}
NEEDS_REMARKS = (S.RESOLVED, S.REJECTED)


class ComplaintService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ComplaintRepository(db)
        self.customers = CustomerRepository(db)
        self.pickups = PickupRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    def _own_customer(self, actor: User):
        customer = self.customers.get_by_user(actor.id)
        if not customer:
            raise BadRequestError("No customer profile is linked to this account")
        return customer

    def get(self, complaint_id: int, actor: User | None = None) -> Complaint:
        c = get_or_404(self.repo, complaint_id, "Complaint")
        if actor and actor.role == UserRole.CUSTOMER and self._own_customer(actor).id != c.customer_id:
            raise ForbiddenError("You can only access your own complaints")
        return c

    def create(self, actor: User, data: ComplaintCreate) -> Complaint:
        if actor.role == UserRole.CUSTOMER:
            customer = self._own_customer(actor)
        else:
            if not data.customer_id:
                raise BadRequestError("customer_id is required when filing on behalf of a customer")
            customer = get_or_404(self.customers, data.customer_id, "Customer")
        if data.pickup_request_id:
            pickup = get_or_404(self.pickups, data.pickup_request_id, "Pickup request")
            if pickup.customer_id != customer.id:
                raise BadRequestError("Pickup request does not belong to this customer")
        with transaction(self.db):
            c = self.repo.add(
                Complaint(
                    complaint_no=self.repo.next_number("CMP"),
                    customer_id=customer.id,
                    pickup_request_id=data.pickup_request_id,
                    category=data.category,
                    description=data.description,
                    priority=data.priority,
                )
            )
            self.repo.add_history(complaint_id=c.id, old_status=None, new_status=c.status.value, remarks="Complaint filed", changed_by_id=actor.id)
            self.audit.log(actor, "COMPLAINT_CREATED", "complaint", c.id, {"category": c.category.value})
            msg = f"{c.complaint_no} ({c.category.value}, {c.priority.value} priority)"
            self.notify.notify_management(NotificationType.CUSTOMER_COMPLAINT, "New customer complaint", msg, "complaint", c.id)
            self.notify.notify(
                NotificationType.CUSTOMER_COMPLAINT, "New customer complaint", msg, role=UserRole.COLLECTION_SUPERVISOR, entity_type="complaint", entity_id=c.id
            )
        return c

    def list(self, actor: User, params: PageParams, **filters):
        if actor.role == UserRole.CUSTOMER:
            filters["customer_id"] = self._own_customer(actor).id
        return paginate(self.db, self.repo.filtered(**filters), params)

    def assign(self, actor: User, complaint_id: int, data: ComplaintAssign) -> Complaint:
        c = self.get(complaint_id)
        if c.status not in (S.OPEN, S.ASSIGNED):
            raise BusinessRuleError(f"A complaint that is {c.status.value} cannot be reassigned")
        if data.assigned_to_id:
            assignee = get_or_404(self.users, data.assigned_to_id, "Assignee")
            if assignee.role == UserRole.CUSTOMER:
                raise BadRequestError("Complaints can only be assigned to staff")
        with transaction(self.db):
            old = c.status
            c.assigned_team = data.assigned_team
            c.assigned_to_id = data.assigned_to_id
            c.status = S.ASSIGNED
            self.repo.add_history(
                complaint_id=c.id, old_status=old.value, new_status=c.status.value, remarks=f"Assigned to {data.assigned_team}", changed_by_id=actor.id
            )
            self.audit.log(actor, "COMPLAINT_ASSIGNED", "complaint", c.id, {"team": data.assigned_team})
            if data.assigned_to_id:
                self.notify.notify(
                    NotificationType.CUSTOMER_COMPLAINT,
                    "Complaint assigned to you",
                    c.complaint_no,
                    user_id=data.assigned_to_id,
                    entity_type="complaint",
                    entity_id=c.id,
                )
        return c

    def update_status(self, actor: User, complaint_id: int, status: ComplaintStatus, remarks: str | None) -> Complaint:
        c = self.get(complaint_id)
        if status not in TRANSITIONS[c.status]:
            raise BusinessRuleError(f"Cannot move a complaint from '{c.status.value}' to '{status.value}'")
        if status in NEEDS_REMARKS and not remarks:
            raise BadRequestError(f"Remarks are required when marking a complaint {status.value}")
        with transaction(self.db):
            old = c.status
            c.status = status
            if status in NEEDS_REMARKS:
                c.resolution_remarks = remarks
            self.repo.add_history(complaint_id=c.id, old_status=old.value, new_status=status.value, remarks=remarks, changed_by_id=actor.id)
            self.audit.log(actor, f"COMPLAINT_{status.value.upper()}", "complaint", c.id, {"from": old.value})
            customer = self.customers.get(c.customer_id)
            if customer and customer.user_id:
                self.notify.notify(
                    NotificationType.CUSTOMER_COMPLAINT,
                    f"Complaint {status.value.replace('_', ' ')}",
                    f"{c.complaint_no} is now {status.value.replace('_', ' ')}",
                    user_id=customer.user_id,
                    entity_type="complaint",
                    entity_id=c.id,
                )
        return c

    def history(self, actor: User, complaint_id: int, params: PageParams):
        self.get(complaint_id, actor)
        return paginate(self.db, self.repo.history(complaint_id), params)
