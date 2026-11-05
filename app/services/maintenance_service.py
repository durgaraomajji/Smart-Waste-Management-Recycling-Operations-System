from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.constants import MAINTENANCE_DUE_WINDOW_DAYS
from app.core.exceptions import BusinessRuleError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import (
    AssignmentStatus,
    MaintenanceStatus,
    MaintenanceType,
    NotificationType,
    Priority,
    UserRole,
    VehicleStatus,
)
from app.models import MaintenanceRequest, MaintenanceSchedule, User, VehicleMaintenance
from app.models.base_model import utcnow
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.maintenance_repository import (
    MaintenanceRecordRepository,
    MaintenanceRepository,
    MaintenanceScheduleRepository,
)
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.maintenance import (
    BreakdownReport,
    MaintenanceComplete,
    MaintenanceRequestCreate,
    ScheduleCreate,
    TechnicianAssign,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.datetime_utils import hours_between
from app.utils.validators import get_or_404

OPEN_STATES = (MaintenanceStatus.REQUESTED, MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS)
ACTIVE_ASSIGNMENTS = (AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS)


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MaintenanceRepository(db)
        self.schedules = MaintenanceScheduleRepository(db)
        self.records = MaintenanceRecordRepository(db)
        self.vehicles = VehicleRepository(db)
        self.assignments = AssignmentRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    # ----------------------------------------------------------------- requests
    def create_request(self, actor: User, data: MaintenanceRequestCreate) -> MaintenanceRequest:
        get_or_404(self.vehicles, data.vehicle_id, "Vehicle")
        with transaction(self.db):
            req = self.repo.add(MaintenanceRequest(reported_by_id=actor.id, **data.model_dump()))
            self.audit.log(actor, "MAINTENANCE_REQUESTED", "maintenance_request", req.id, {"vehicle_id": req.vehicle_id})
        return req

    def report_breakdown(self, actor: User, data: BreakdownReport) -> MaintenanceRequest:
        vehicle = get_or_404(self.vehicles, data.vehicle_id, "Vehicle")
        with transaction(self.db):
            req = self.repo.add(
                MaintenanceRequest(
                    vehicle_id=vehicle.id,
                    maintenance_type=MaintenanceType.BREAKDOWN,
                    description=data.description,
                    priority=Priority.URGENT,
                    reported_by_id=actor.id,
                )
            )
            vehicle.status = VehicleStatus.BROKEN_DOWN
            pending = self.assignments.count(
                self.assignments.select().where(
                    self.assignments.model.vehicle_id == vehicle.id, self.assignments.model.status == AssignmentStatus.ASSIGNED
                )
            )
            self.audit.log(actor, "VEHICLE_BREAKDOWN_REPORTED", "vehicle", vehicle.id, {"request_id": req.id, "pending_assignments": pending})
            msg = f"{vehicle.registration_number} broke down: {data.description}"
            if pending:
                msg += f". {pending} upcoming collection(s) need reassignment."
            self.notify.notify_management(NotificationType.VEHICLE_BREAKDOWN, "Vehicle breakdown", msg, "vehicle", vehicle.id)
            self.notify.notify(
                NotificationType.VEHICLE_BREAKDOWN, "Vehicle breakdown", msg, role=UserRole.COLLECTION_SUPERVISOR, entity_type="vehicle", entity_id=vehicle.id
            )
        return req

    def get(self, request_id: int) -> MaintenanceRequest:
        return get_or_404(self.repo, request_id, "Maintenance request")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def assign_technician(self, actor: User, request_id: int, data: TechnicianAssign) -> MaintenanceRequest:
        req = self.get(request_id)
        if req.status not in (MaintenanceStatus.REQUESTED, MaintenanceStatus.SCHEDULED):
            raise BusinessRuleError(f"Cannot assign a technician to a request that is {req.status.value}")
        tech = get_or_404(self.users, data.technician_id, "Technician")
        if tech.role == UserRole.CUSTOMER or not tech.is_active:
            raise BusinessRuleError("Technician must be an active staff member")
        with transaction(self.db):
            req.technician_id = tech.id
            req.scheduled_date = data.scheduled_date or req.scheduled_date
            req.status = MaintenanceStatus.SCHEDULED
            self.audit.log(actor, "MAINTENANCE_TECHNICIAN_ASSIGNED", "maintenance_request", req.id, {"technician_id": tech.id})
        return req

    def start(self, actor: User, request_id: int) -> MaintenanceRequest:
        req = self.get(request_id)
        if req.status not in (MaintenanceStatus.REQUESTED, MaintenanceStatus.SCHEDULED):
            raise BusinessRuleError(f"Cannot start a request that is {req.status.value}")
        vehicle = self.vehicles.get(req.vehicle_id)
        if req.maintenance_type != MaintenanceType.BREAKDOWN:
            busy = self.assignments.count(
                self.assignments.select().where(
                    self.assignments.model.vehicle_id == vehicle.id, self.assignments.model.status.in_(ACTIVE_ASSIGNMENTS)
                )
            )
            if busy:
                raise BusinessRuleError("Vehicle has active collection assignments - reassign them before servicing")
        with transaction(self.db):
            req.status = MaintenanceStatus.IN_PROGRESS
            req.started_at = utcnow()
            if vehicle.status != VehicleStatus.BROKEN_DOWN:
                vehicle.status = VehicleStatus.UNDER_MAINTENANCE
            self.audit.log(actor, "MAINTENANCE_STARTED", "maintenance_request", req.id, {"vehicle_id": vehicle.id})
        return req

    def complete(self, actor: User, request_id: int, data: MaintenanceComplete) -> MaintenanceRequest:
        req = self.get(request_id)
        if req.status != MaintenanceStatus.IN_PROGRESS:
            raise BusinessRuleError("Only requests in progress can be completed")
        vehicle = self.vehicles.get(req.vehicle_id)
        now = utcnow()
        # downtime clock starts at the breakdown report, or at the start of planned work
        downtime_from = req.created_at if req.maintenance_type == MaintenanceType.BREAKDOWN else (req.started_at or now)
        with transaction(self.db):
            req.status = MaintenanceStatus.COMPLETED
            req.completed_at = now
            req.cost = data.cost
            req.downtime_hours = hours_between(downtime_from, now)
            self.records.add(
                VehicleMaintenance(
                    vehicle_id=vehicle.id,
                    maintenance_request_id=req.id,
                    service_date=now.date(),
                    description=data.notes or req.description,
                    cost=data.cost,
                    performed_by=data.performed_by,
                    odometer_km=data.odometer_km,
                )
            )
            vehicle.last_service_date = now.date()
            self._roll_schedules(vehicle.id, now.date())
            self.db.flush()  # autoflush is off - make the COMPLETED status visible to the count below
            still_open = self.repo.open_for_vehicle(vehicle.id)
            if vehicle.status in (VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.BROKEN_DOWN) and not still_open:
                vehicle.status = VehicleStatus.AVAILABLE
            self.audit.log(
                actor, "MAINTENANCE_COMPLETED", "maintenance_request", req.id, {"cost": data.cost, "downtime_hours": req.downtime_hours}
            )
        return req

    def cancel(self, actor: User, request_id: int) -> MaintenanceRequest:
        req = self.get(request_id)
        if req.status not in (MaintenanceStatus.REQUESTED, MaintenanceStatus.SCHEDULED):
            raise BusinessRuleError("Only requests that have not started can be cancelled")
        with transaction(self.db):
            req.status = MaintenanceStatus.CANCELLED
            self.audit.log(actor, "MAINTENANCE_CANCELLED", "maintenance_request", req.id)
        return req

    # --------------------------------------------------------------- schedules
    def create_schedule(self, actor: User, data: ScheduleCreate) -> MaintenanceSchedule:
        vehicle = get_or_404(self.vehicles, data.vehicle_id, "Vehicle")
        base = data.last_service_date or date.today()
        with transaction(self.db):
            sched = self.schedules.add(
                MaintenanceSchedule(
                    vehicle_id=vehicle.id,
                    description=data.description,
                    interval_days=data.interval_days,
                    last_service_date=data.last_service_date,
                    next_due_date=base + timedelta(days=data.interval_days),
                )
            )
            self._sync_vehicle_next_service(vehicle.id)
            self.audit.log(actor, "MAINTENANCE_SCHEDULE_CREATED", "maintenance_schedule", sched.id, {"vehicle_id": vehicle.id})
        return sched

    def list_schedules(self, vehicle_id: int, params: PageParams):
        return paginate(self.db, self.schedules.for_vehicle(vehicle_id), params)

    def _roll_schedules(self, vehicle_id: int, serviced_on: date) -> None:
        for s in self.db.scalars(self.schedules.select().where(MaintenanceSchedule.vehicle_id == vehicle_id, MaintenanceSchedule.is_active.is_(True))):
            s.last_service_date = serviced_on
            s.next_due_date = serviced_on + timedelta(days=s.interval_days)
        self.db.flush()
        self._sync_vehicle_next_service(vehicle_id)

    def _sync_vehicle_next_service(self, vehicle_id: int) -> None:
        dues = [
            s.next_due_date
            for s in self.db.scalars(self.schedules.select().where(MaintenanceSchedule.vehicle_id == vehicle_id, MaintenanceSchedule.is_active.is_(True)))
        ]
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle:
            vehicle.next_service_date = min(dues) if dues else None

    # ----------------------------------------------------------- due reminders
    def raise_due_notifications(self) -> int:
        """Creates MAINTENANCE_DUE alerts for schedules due within the window. Idempotent while an alert is unread."""
        cutoff = date.today() + timedelta(days=MAINTENANCE_DUE_WINDOW_DAYS)
        notifications = NotificationRepository(self.db)
        created = 0
        with transaction(self.db):
            for s in self.schedules.due_before(cutoff):
                if notifications.exists_unread(NotificationType.MAINTENANCE_DUE, "maintenance_schedule", s.id):
                    continue
                vehicle = self.vehicles.get(s.vehicle_id)
                label = vehicle.registration_number if vehicle else f"vehicle {s.vehicle_id}"
                state = "overdue since" if s.next_due_date < date.today() else "due on"
                self.notify.notify_management(
                    NotificationType.MAINTENANCE_DUE,
                    "Vehicle maintenance due",
                    f"{label}: {s.description} {state} {s.next_due_date}",
                    "maintenance_schedule",
                    s.id,
                )
                created += 1
        return created

    def history(self, vehicle_id: int, params: PageParams):
        get_or_404(self.vehicles, vehicle_id, "Vehicle")
        return paginate(self.db, self.records.for_vehicle(vehicle_id), params)
