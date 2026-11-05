from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ForbiddenError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import AssignmentStatus, CollectionStatus, NotificationType, PickupStatus, UserRole
from app.models import CollectionRecord, User
from app.models.base_model import utcnow
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.collection_repository import CollectionRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.pickup_repository import PickupRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.collection_tracking import CollectionComplete, CollectionIncomplete, CollectionStart
from app.services.assignment_service import AssignmentService, refresh_resource_status
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.validators import get_or_404

STARTABLE_PICKUP = (PickupStatus.ASSIGNED, PickupStatus.SCHEDULED)


class CollectionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CollectionRepository(db)
        self.assignments = AssignmentRepository(db)
        self.pickups = PickupRepository(db)
        self.vehicles = VehicleRepository(db)
        self.customers = CustomerRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    # ---------------------------------------------------------------- access
    def _crew_or_staff(self, actor: User, assignment) -> None:
        if actor.role in (UserRole.DRIVER, UserRole.FIELD_WORKER):
            if not AssignmentService(self.db).is_crew_member(assignment, actor):
                raise ForbiddenError("This collection is not assigned to you")

    def get(self, record_id: int) -> CollectionRecord:
        return get_or_404(self.repo, record_id, "Collection record")

    def list(self, actor: User, params: PageParams, **filters):
        if actor.role == UserRole.CUSTOMER:
            customer = self.customers.get_by_user(actor.id)
            filters["customer_id"] = customer.id if customer else -1
        return paginate(self.db, self.repo.filtered(**filters), params)

    # ----------------------------------------------------------------- start
    def start(self, actor: User, data: CollectionStart) -> CollectionRecord:
        a = get_or_404(self.assignments, data.assignment_id, "Assignment")
        self._crew_or_staff(actor, a)
        if a.status != AssignmentStatus.ASSIGNED:
            raise BusinessRuleError(f"Assignment cannot be started (status: {a.status.value})")
        pickup = get_or_404(self.pickups, a.pickup_request_id, "Pickup request")
        if pickup.status not in STARTABLE_PICKUP:
            raise BusinessRuleError(f"Pickup is '{pickup.status.value}' and cannot be collected")
        with transaction(self.db):
            a.status = AssignmentStatus.IN_PROGRESS
            record = self.repo.add(
                CollectionRecord(
                    assignment_id=a.id,
                    pickup_request_id=pickup.id,
                    status=CollectionStatus.STARTED,
                    started_at=utcnow(),
                    remarks=data.remarks,
                    recorded_by_id=actor.id,
                )
            )
            refresh_resource_status(self.db, a.driver_id, a.vehicle_id, [w.id for w in a.workers])
            self.audit.log(actor, "COLLECTION_STARTED", "collection_record", record.id, {"assignment_id": a.id})
        return record

    # -------------------------------------------------------------- complete
    def complete(self, actor: User, record_id: int, data: CollectionComplete) -> CollectionRecord:
        record = self._open_record(actor, record_id)
        a = self.assignments.get(record.assignment_id)
        vehicle = self.vehicles.get(a.vehicle_id)
        if vehicle and data.collected_quantity_kg > vehicle.capacity_kg:
            raise BusinessRuleError(f"Collected quantity exceeds vehicle capacity ({vehicle.capacity_kg} kg)")
        with transaction(self.db):
            record.status = CollectionStatus.COMPLETED
            record.completed_at = utcnow()
            record.collected_quantity_kg = data.collected_quantity_kg
            record.remarks = data.remarks or record.remarks
            record.photo_urls = [str(u) for u in data.photo_urls]
            a.status = AssignmentStatus.COMPLETED
            pickup = self.pickups.get(record.pickup_request_id)
            pickup.status = PickupStatus.COLLECTED
            self.db.flush()
            self.assignments.add_history(
                assignment_id=a.id, action="completed", new_values={"collected_kg": data.collected_quantity_kg}, changed_by_id=actor.id
            )
            refresh_resource_status(self.db, a.driver_id, a.vehicle_id, [w.id for w in a.workers])
            self.audit.log(
                actor, "COLLECTION_COMPLETED", "collection_record", record.id, {"pickup": pickup.request_no, "kg": data.collected_quantity_kg}
            )
        return record

    # ------------------------------------------------------------ incomplete
    def incomplete(self, actor: User, record_id: int, data: CollectionIncomplete) -> CollectionRecord:
        record = self._open_record(actor, record_id)
        a = self.assignments.get(record.assignment_id)
        if data.missed and data.collected_quantity_kg:
            raise BusinessRuleError("A missed pickup cannot have a collected quantity")
        if not data.missed and data.collected_quantity_kg <= 0:
            raise BusinessRuleError("Provide the partially collected quantity, or mark the pickup as missed")
        with transaction(self.db):
            record.status = CollectionStatus.MISSED if data.missed else CollectionStatus.INCOMPLETE
            record.completed_at = utcnow()
            record.collected_quantity_kg = data.collected_quantity_kg
            record.incomplete_reason = data.reason
            record.photo_urls = [str(u) for u in data.photo_urls]
            a.status = AssignmentStatus.COMPLETED
            pickup = self.pickups.get(record.pickup_request_id)
            pickup.status = PickupStatus.APPROVED  # back in the queue so it can be re-assigned
            pickup.status_reason = f"Previous attempt: {data.reason}"
            self.db.flush()
            self.assignments.add_history(
                assignment_id=a.id, action="missed" if data.missed else "incomplete", remarks=data.reason, changed_by_id=actor.id
            )
            refresh_resource_status(self.db, a.driver_id, a.vehicle_id, [w.id for w in a.workers])
            self.audit.log(
                actor, "COLLECTION_MISSED" if data.missed else "COLLECTION_INCOMPLETE", "collection_record", record.id, {"reason": data.reason}
            )
            self.notify.notify_management(
                NotificationType.MISSED_COLLECTION,
                "Missed / incomplete collection",
                f"{pickup.request_no}: {data.reason}",
                "pickup_request",
                pickup.id,
            )
            customer = self.customers.get(pickup.customer_id)
            if customer and customer.user_id:
                self.notify.notify(
                    NotificationType.MISSED_COLLECTION,
                    "We could not complete your pickup",
                    f"Request {pickup.request_no} will be rescheduled. Reason: {data.reason}",
                    user_id=customer.user_id,
                    entity_type="pickup_request",
                    entity_id=pickup.id,
                )
        return record

    # ---------------------------------------------------------------- helpers
    def _open_record(self, actor: User, record_id: int) -> CollectionRecord:
        record = self.get(record_id)
        a = self.assignments.get(record.assignment_id)
        self._crew_or_staff(actor, a)
        if record.status != CollectionStatus.STARTED:
            raise BusinessRuleError(f"Collection is already {record.status.value}")
        return record
