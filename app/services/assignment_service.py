from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, BusinessRuleError, ForbiddenError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import (
    AssignmentStatus,
    NotificationType,
    PickupStatus,
    UserRole,
    VehicleStatus,
    WorkforceStatus,
)
from app.models import CollectionAssignment, FieldWorker, PickupRequest, User
from app.repositories.assignment_repository import ACTIVE, AssignmentRepository
from app.repositories.pickup_repository import PickupRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.workforce_repository import DriverRepository, WorkerRepository
from app.schemas.collection_assignment import AssignmentCreate, AssignmentReassign
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.validators import get_or_404

PERSON_ASSIGNABLE = (WorkforceStatus.AVAILABLE, WorkforceStatus.ASSIGNED)
VEHICLE_ASSIGNABLE = (VehicleStatus.AVAILABLE, VehicleStatus.ASSIGNED, VehicleStatus.IN_SERVICE)


def refresh_resource_status(db: Session, driver_id: int | None = None, vehicle_id: int | None = None, worker_ids: list[int] | None = None) -> None:
    """Recompute ASSIGNED / AVAILABLE flags after an assignment changes.

    Resources that are on leave, in maintenance, broken down, retired etc. are never touched.
    """
    repo = AssignmentRepository(db)

    def active_for(column, value):
        return repo.count(repo.select().where(column == value, CollectionAssignment.status.in_(ACTIVE))) > 0

    if driver_id:
        d = DriverRepository(db).get(driver_id)
        if d and d.status in PERSON_ASSIGNABLE:
            d.status = WorkforceStatus.ASSIGNED if active_for(CollectionAssignment.driver_id, driver_id) else WorkforceStatus.AVAILABLE
    if vehicle_id:
        v = VehicleRepository(db).get(vehicle_id)
        if v and v.status in VEHICLE_ASSIGNABLE:
            in_progress = repo.count(
                repo.select().where(CollectionAssignment.vehicle_id == vehicle_id, CollectionAssignment.status == AssignmentStatus.IN_PROGRESS)
            )
            if in_progress:
                v.status = VehicleStatus.IN_SERVICE
            elif active_for(CollectionAssignment.vehicle_id, vehicle_id):
                v.status = VehicleStatus.ASSIGNED
            else:
                v.status = VehicleStatus.AVAILABLE
    for wid in worker_ids or []:
        w = WorkerRepository(db).get(wid)
        if w and w.status in PERSON_ASSIGNABLE:
            busy = repo.count(repo.for_worker(wid).where(CollectionAssignment.status.in_(ACTIVE))) > 0
            w.status = WorkforceStatus.ASSIGNED if busy else WorkforceStatus.AVAILABLE
    db.flush()


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AssignmentRepository(db)
        self.pickups = PickupRepository(db)
        self.drivers = DriverRepository(db)
        self.workers = WorkerRepository(db)
        self.vehicles = VehicleRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    # ------------------------------------------------------------- validation
    def _validate_resources(
        self,
        pickup: PickupRequest,
        driver_id: int,
        vehicle_id: int,
        worker_ids: list[int],
        when: datetime,
        exclude_id: int | None = None,
    ):
        """Capacity + availability checks shared by assign() and reassign()."""
        if when.date() < date.today():
            raise BadRequestError("Collection cannot be scheduled in the past")

        driver = get_or_404(self.drivers, driver_id, "Driver")
        if driver.status not in PERSON_ASSIGNABLE:
            raise BusinessRuleError(f"Driver is not available (status: {driver.status.value})")
        if driver.license_expiry <= when.date():
            raise BusinessRuleError("Driver's licence will be expired on the collection date")
        if self.repo.driver_busy(driver.id, when, exclude_id):
            raise BusinessRuleError("Driver already has a collection at that time")

        vehicle = get_or_404(self.vehicles, vehicle_id, "Vehicle")
        if vehicle.status not in VEHICLE_ASSIGNABLE:
            raise BusinessRuleError(f"Vehicle is not available (status: {vehicle.status.value})")
        if vehicle.capacity_kg < pickup.estimated_quantity_kg:
            raise BusinessRuleError(
                f"Vehicle capacity ({vehicle.capacity_kg} kg) is below the estimated quantity ({pickup.estimated_quantity_kg} kg)"
            )
        if self.repo.vehicle_busy(vehicle.id, when, exclude_id):
            raise BusinessRuleError("Vehicle already has a collection at that time")

        workers: list[FieldWorker] = []
        for wid in dict.fromkeys(worker_ids):  # de-duplicate, keep order
            w = get_or_404(self.workers, wid, "Field worker")
            if w.status not in PERSON_ASSIGNABLE:
                raise BusinessRuleError(f"Field worker {w.full_name} is not available (status: {w.status.value})")
            if self.repo.worker_busy(w.id, when, exclude_id):
                raise BusinessRuleError(f"Field worker {w.full_name} already has a collection at that time")
            workers.append(w)
        return driver, vehicle, workers

    # ------------------------------------------------------------------ assign
    def assign(self, actor: User, data: AssignmentCreate) -> CollectionAssignment:
        pickup = get_or_404(self.pickups, data.pickup_request_id, "Pickup request")
        if pickup.status != PickupStatus.APPROVED:
            raise BusinessRuleError(f"Only approved requests can be assigned (current status: {pickup.status.value})")
        if self.repo.active_for_pickup(pickup.id):
            raise BusinessRuleError("Pickup already has an active assignment - use reassign instead")
        driver, vehicle, workers = self._validate_resources(pickup, data.driver_id, data.vehicle_id, data.worker_ids, data.scheduled_at)

        with transaction(self.db):
            a = self.repo.add(
                CollectionAssignment(
                    pickup_request_id=pickup.id,
                    driver_id=driver.id,
                    vehicle_id=vehicle.id,
                    scheduled_at=data.scheduled_at,
                    assigned_by_id=actor.id,
                    remarks=data.remarks,
                )
            )
            a.workers = workers
            pickup.status = PickupStatus.ASSIGNED
            self.db.flush()
            self.repo.add_history(
                assignment_id=a.id,
                action="assigned",
                new_values=self._snapshot(a),
                changed_by_id=actor.id,
                remarks=data.remarks,
            )
            refresh_resource_status(self.db, driver.id, vehicle.id, [w.id for w in workers])
            self.audit.log(actor, "ASSIGNMENT_CREATED", "collection_assignment", a.id, self._snapshot(a))
            self._notify_crew(a, driver, workers, pickup, "New collection assignment")
        return a

    # ---------------------------------------------------------------- reassign
    def reassign(self, actor: User, assignment_id: int, data: AssignmentReassign) -> CollectionAssignment:
        a = self.get(assignment_id)
        if a.status != AssignmentStatus.ASSIGNED:
            raise BusinessRuleError("Only collections that have not started can be reassigned")
        pickup = get_or_404(self.pickups, a.pickup_request_id, "Pickup request")

        old = self._snapshot(a)
        old_driver, old_vehicle, old_workers = a.driver_id, a.vehicle_id, [w.id for w in a.workers]
        new_driver = data.driver_id or a.driver_id
        new_vehicle = data.vehicle_id or a.vehicle_id
        new_workers = data.worker_ids if data.worker_ids is not None else old_workers
        new_when = data.scheduled_at or a.scheduled_at
        driver, vehicle, workers = self._validate_resources(pickup, new_driver, new_vehicle, new_workers, new_when, exclude_id=a.id)

        with transaction(self.db):
            a.driver_id, a.vehicle_id, a.scheduled_at = driver.id, vehicle.id, new_when
            a.workers = workers
            if data.remarks:
                a.remarks = data.remarks
            if pickup.status == PickupStatus.SCHEDULED:
                pickup.status = PickupStatus.ASSIGNED  # slot must be re-confirmed
            self.db.flush()
            self.repo.add_history(
                assignment_id=a.id, action="reassigned", old_values=old, new_values=self._snapshot(a), changed_by_id=actor.id, remarks=data.remarks
            )
            refresh_resource_status(self.db, old_driver, old_vehicle, old_workers)
            refresh_resource_status(self.db, driver.id, vehicle.id, [w.id for w in workers])
            self.audit.log(actor, "ASSIGNMENT_CHANGED", "collection_assignment", a.id, {"old": old, "new": self._snapshot(a)})
            self._notify_crew(a, driver, workers, pickup, "Collection assignment updated")
        return a

    def set_schedule(self, actor: User, assignment_id: int, when: datetime) -> CollectionAssignment:
        a = self.get(assignment_id)
        if a.status != AssignmentStatus.ASSIGNED:
            raise BusinessRuleError("Only collections that have not started can be scheduled")
        pickup = get_or_404(self.pickups, a.pickup_request_id, "Pickup request")
        self._validate_resources(pickup, a.driver_id, a.vehicle_id, [w.id for w in a.workers], when, exclude_id=a.id)
        with transaction(self.db):
            old = a.scheduled_at
            a.scheduled_at = when
            pickup.status = PickupStatus.SCHEDULED
            self.repo.add_history(
                assignment_id=a.id,
                action="scheduled",
                old_values={"scheduled_at": old.isoformat()},
                new_values={"scheduled_at": when.isoformat()},
                changed_by_id=actor.id,
            )
            self.audit.log(actor, "ASSIGNMENT_SCHEDULED", "collection_assignment", a.id, {"scheduled_at": when.isoformat()})
        return a

    # ----------------------------------------------------------------- cancel
    def cancel_for_pickup(self, actor: User, pickup: PickupRequest) -> None:
        """Called inside the pickup-cancel transaction; releases the crew and vehicle."""
        a = self.repo.active_for_pickup(pickup.id)
        if not a:
            return
        if a.status == AssignmentStatus.IN_PROGRESS:
            raise BusinessRuleError("Collection is already in progress and cannot be cancelled")
        a.status = AssignmentStatus.CANCELLED
        self.db.flush()
        self.repo.add_history(assignment_id=a.id, action="cancelled", old_values=self._snapshot(a), changed_by_id=actor.id)
        refresh_resource_status(self.db, a.driver_id, a.vehicle_id, [w.id for w in a.workers])

    # ------------------------------------------------------------------ reads
    def get(self, assignment_id: int, actor: User | None = None) -> CollectionAssignment:
        a = get_or_404(self.repo, assignment_id, "Assignment")
        if actor and actor.role in (UserRole.DRIVER, UserRole.FIELD_WORKER) and not self.is_crew_member(a, actor):
            raise ForbiddenError("This assignment is not yours")
        return a

    def list(self, actor: User, params: PageParams, **filters):
        if actor.role == UserRole.DRIVER:
            driver = self.drivers.get_by(user_id=actor.id)
            filters["driver_id"] = driver.id if driver else -1
            return paginate(self.db, self.repo.filtered(**filters), params)
        if actor.role == UserRole.FIELD_WORKER:
            worker = self.workers.get_by(user_id=actor.id)
            return paginate(self.db, self.repo.for_worker(worker.id if worker else -1), params)
        return paginate(self.db, self.repo.filtered(**filters), params)

    def history(self, assignment_id: int, params: PageParams, actor: User | None = None):
        self.get(assignment_id, actor)
        return paginate(self.db, self.repo.history(assignment_id), params)

    # ---------------------------------------------------------------- helpers
    def is_crew_member(self, a: CollectionAssignment, user: User) -> bool:
        driver = self.drivers.get(a.driver_id)
        if driver and driver.user_id == user.id:
            return True
        return any(w.user_id == user.id for w in a.workers)

    @staticmethod
    def _snapshot(a: CollectionAssignment) -> dict:
        return {
            "driver_id": a.driver_id,
            "vehicle_id": a.vehicle_id,
            "worker_ids": sorted(w.id for w in a.workers),
            "scheduled_at": a.scheduled_at.isoformat(),
            "status": a.status.value if a.status else None,
        }

    def _notify_crew(self, a, driver, workers, pickup, title: str) -> None:
        msg = f"{pickup.request_no} scheduled for {a.scheduled_at:%Y-%m-%d %H:%M}"
        for uid in [driver.user_id] + [w.user_id for w in workers]:
            if uid:
                self.notify.notify(
                    NotificationType.COLLECTION_ASSIGNMENT, title, msg, user_id=uid, entity_type="collection_assignment", entity_id=a.id
                )
