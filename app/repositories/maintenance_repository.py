from datetime import date

from app.enums import MaintenanceStatus, MaintenanceType
from app.models import MaintenanceRequest, MaintenanceSchedule, VehicleMaintenance
from app.repositories.base_repository import BaseRepository


class MaintenanceRepository(BaseRepository[MaintenanceRequest]):
    model = MaintenanceRequest

    def filtered(self, vehicle_id: int | None = None, status: MaintenanceStatus | None = None, maintenance_type: MaintenanceType | None = None):
        stmt = self.select()
        if vehicle_id:
            stmt = stmt.where(MaintenanceRequest.vehicle_id == vehicle_id)
        if status:
            stmt = stmt.where(MaintenanceRequest.status == status)
        if maintenance_type:
            stmt = stmt.where(MaintenanceRequest.maintenance_type == maintenance_type)
        return stmt.order_by(MaintenanceRequest.id.desc())

    def open_for_vehicle(self, vehicle_id: int) -> int:
        open_states = (MaintenanceStatus.REQUESTED, MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS)
        return self.count(self.select().where(MaintenanceRequest.vehicle_id == vehicle_id, MaintenanceRequest.status.in_(open_states)))


class MaintenanceScheduleRepository(BaseRepository[MaintenanceSchedule]):
    model = MaintenanceSchedule

    def due_before(self, cutoff: date):
        return self.db.scalars(
            self.select().where(MaintenanceSchedule.is_active.is_(True), MaintenanceSchedule.next_due_date <= cutoff)
        ).all()

    def for_vehicle(self, vehicle_id: int):
        return self.select().where(MaintenanceSchedule.vehicle_id == vehicle_id).order_by(MaintenanceSchedule.next_due_date)


class MaintenanceRecordRepository(BaseRepository[VehicleMaintenance]):
    model = VehicleMaintenance

    def for_vehicle(self, vehicle_id: int):
        return self.select().where(VehicleMaintenance.vehicle_id == vehicle_id).order_by(VehicleMaintenance.service_date.desc())
