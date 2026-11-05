from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, BusinessRuleError, ConflictError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import UserRole, WorkforceStatus
from app.models import Driver, FieldWorker, User
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workforce_repository import DriverRepository, WorkerRepository
from app.schemas.workforce import DriverCreate, WorkerCreate, WorkforceUpdate
from app.services.audit_service import AuditService
from app.utils.validators import get_or_404, require_user_with_role, validate_phone

SUPERVISORS = (UserRole.COLLECTION_SUPERVISOR, UserRole.OPERATIONS_MANAGER, UserRole.SUPER_ADMIN)
MANUAL_STATUSES = (WorkforceStatus.AVAILABLE, WorkforceStatus.ON_LEAVE, WorkforceStatus.INACTIVE)


class WorkforceService:
    """Drivers and field workers share most behaviour - `kind` selects the repository."""

    def __init__(self, db: Session):
        self.db = db
        self.drivers = DriverRepository(db)
        self.workers = WorkerRepository(db)
        self.users = UserRepository(db)
        self.assignments = AssignmentRepository(db)
        self.audit = AuditService(db)

    def _repo(self, kind: str):
        return self.drivers if kind == "driver" else self.workers

    # ------------------------------------------------------------------ create
    def create_driver(self, actor: User, data: DriverCreate) -> Driver:
        if self.drivers.exists(employee_code=data.employee_code):
            raise ConflictError("Employee code already exists")
        if self.drivers.exists(license_number=data.license_number):
            raise ConflictError("A driver with this licence number already exists")
        validate_phone(data.phone)
        self._validate_links(data.user_id, data.supervisor_id, UserRole.DRIVER)
        with transaction(self.db):
            driver = self.drivers.add(Driver(**data.model_dump()))
            self.audit.log(actor, "DRIVER_REGISTERED", "driver", driver.id)
        return driver

    def create_worker(self, actor: User, data: WorkerCreate) -> FieldWorker:
        if self.workers.exists(employee_code=data.employee_code):
            raise ConflictError("Employee code already exists")
        validate_phone(data.phone)
        self._validate_links(data.user_id, data.supervisor_id, UserRole.FIELD_WORKER)
        with transaction(self.db):
            worker = self.workers.add(FieldWorker(**data.model_dump()))
            self.audit.log(actor, "WORKER_REGISTERED", "field_worker", worker.id)
        return worker

    def _validate_links(self, user_id: int | None, supervisor_id: int | None, role: UserRole) -> None:
        if user_id:
            require_user_with_role(self.users, user_id, (role,), f"Linked user ({role.value})")
        if supervisor_id:
            require_user_with_role(self.users, supervisor_id, SUPERVISORS, "Supervisor")

    # -------------------------------------------------------------------- reads
    def get(self, kind: str, id_: int):
        return get_or_404(self._repo(kind), id_, "Driver" if kind == "driver" else "Field worker")

    def list(self, kind: str, params: PageParams, **filters):
        return paginate(self.db, self._repo(kind).filtered(**filters), params)

    # ------------------------------------------------------------------ updates
    def update(self, actor: User, kind: str, id_: int, data: WorkforceUpdate):
        person = self.get(kind, id_)
        values = data.model_dump(exclude_unset=True)
        if "phone" in values:
            validate_phone(values["phone"])
        if values.get("supervisor_id"):
            require_user_with_role(self.users, values["supervisor_id"], SUPERVISORS, "Supervisor")
        with transaction(self.db):
            self._repo(kind).update(person, values)
            self.audit.log(actor, f"{kind.upper()}_UPDATED", kind, person.id, values)
        return person

    def assign_supervisor(self, actor: User, kind: str, id_: int, supervisor_id: int):
        return self.update(actor, kind, id_, WorkforceUpdate(supervisor_id=supervisor_id))

    def set_status(self, actor: User, kind: str, id_: int, status: WorkforceStatus):
        person = self.get(kind, id_)
        if status not in MANUAL_STATUSES:
            raise BadRequestError("'assigned' is set automatically by the assignment workflow")
        if status in (WorkforceStatus.ON_LEAVE, WorkforceStatus.INACTIVE) and person.status == WorkforceStatus.ASSIGNED:
            raise BusinessRuleError("Person has active assignments - reassign them before changing availability")
        with transaction(self.db):
            old = person.status
            person.status = status
            self.audit.log(actor, f"{kind.upper()}_STATUS_CHANGED", kind, person.id, {"from": old.value, "to": status.value})
        return person

    def delete(self, actor: User, kind: str, id_: int) -> None:
        person = self.get(kind, id_)
        if person.status == WorkforceStatus.ASSIGNED:
            raise BusinessRuleError("Person has active assignments and cannot be deleted")
        with transaction(self.db):
            self._repo(kind).soft_delete(person)
            self.audit.log(actor, f"{kind.upper()}_DELETED", kind, person.id)

    # ------------------------------------------------------------------ history
    def history(self, kind: str, id_: int, params: PageParams):
        """Workforce history = every collection assignment the person has been part of."""
        self.get(kind, id_)
        stmt = self.assignments.filtered(driver_id=id_) if kind == "driver" else self.assignments.for_worker(id_)
        page = paginate(self.db, stmt, params)
        page["items"] = [
            {
                "assignment_id": a.id,
                "pickup_request_id": a.pickup_request_id,
                "vehicle_id": a.vehicle_id,
                "scheduled_at": a.scheduled_at,
                "status": a.status.value,
            }
            for a in page["items"]
        ]
        return page
