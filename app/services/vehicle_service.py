from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import VehicleStatus
from app.models import User, Vehicle
from app.repositories.maintenance_repository import MaintenanceRecordRepository, MaintenanceRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.audit_service import AuditService
from app.utils.validators import get_or_404

# statuses in which a vehicle may be given new work
ASSIGNABLE = (VehicleStatus.AVAILABLE, VehicleStatus.ASSIGNED, VehicleStatus.IN_SERVICE)
# statuses a person may set by hand (ASSIGNED / IN_SERVICE are controlled by the assignment workflow)
MANUAL = (VehicleStatus.AVAILABLE, VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.BROKEN_DOWN, VehicleStatus.RETIRED)


class VehicleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VehicleRepository(db)
        self.maintenance = MaintenanceRepository(db)
        self.records = MaintenanceRecordRepository(db)
        self.audit = AuditService(db)

    def create(self, actor: User, data: VehicleCreate) -> Vehicle:
        if self.repo.exists(registration_number=data.registration_number):
            raise ConflictError("A vehicle with this registration number already exists")
        with transaction(self.db):
            vehicle = self.repo.add(Vehicle(**data.model_dump()))
            self.audit.log(actor, "VEHICLE_REGISTERED", "vehicle", vehicle.id, {"reg": vehicle.registration_number})
        return vehicle

    def get(self, vehicle_id: int) -> Vehicle:
        return get_or_404(self.repo, vehicle_id, "Vehicle")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def update(self, actor: User, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        vehicle = self.get(vehicle_id)
        values = data.model_dump(exclude_unset=True)
        with transaction(self.db):
            self.repo.update(vehicle, values)
            self.audit.log(actor, "VEHICLE_UPDATED", "vehicle", vehicle.id, values)
        return vehicle

    def set_status(self, actor: User, vehicle_id: int, status: VehicleStatus) -> Vehicle:
        vehicle = self.get(vehicle_id)
        if status not in MANUAL:
            raise BusinessRuleError("'assigned' and 'in_service' are set automatically by the assignment workflow")
        if status == VehicleStatus.AVAILABLE and self.maintenance.open_for_vehicle(vehicle.id):
            raise BusinessRuleError("Vehicle has open maintenance requests and cannot be marked available")
        with transaction(self.db):
            old = vehicle.status
            vehicle.status = status
            self.audit.log(actor, "VEHICLE_STATUS_CHANGED", "vehicle", vehicle.id, {"from": old.value, "to": status.value})
        return vehicle

    def delete(self, actor: User, vehicle_id: int) -> None:
        vehicle = self.get(vehicle_id)
        if vehicle.status in (VehicleStatus.ASSIGNED, VehicleStatus.IN_SERVICE):
            raise BusinessRuleError("Vehicle has active work and cannot be deleted")
        with transaction(self.db):
            self.repo.soft_delete(vehicle)
            self.audit.log(actor, "VEHICLE_DELETED", "vehicle", vehicle.id)

    # ------------------------------------------------------------- availability
    def availability(self, vehicle_id: int) -> dict:
        vehicle = self.get(vehicle_id)
        reason = None
        if vehicle.status not in ASSIGNABLE:
            reason = f"Vehicle status is '{vehicle.status.value}'"
        elif vehicle.next_service_date and vehicle.next_service_date < date.today():
            reason = "Preventive service is overdue"
        return {
            "vehicle_id": vehicle.id,
            "registration_number": vehicle.registration_number,
            "available": reason is None,
            "reason": reason,
        }

    def maintenance_history(self, vehicle_id: int, params: PageParams):
        self.get(vehicle_id)
        return paginate(self.db, self.records.for_vehicle(vehicle_id), params)
