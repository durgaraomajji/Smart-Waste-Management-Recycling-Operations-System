from app.enums import VehicleStatus, VehicleType
from app.models import Vehicle
from app.repositories.base_repository import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    model = Vehicle

    def filtered(
        self,
        status: VehicleStatus | None = None,
        vehicle_type: VehicleType | None = None,
        zone_id: int | None = None,
        search: str | None = None,
        min_capacity: float | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(Vehicle.status == status)
        if vehicle_type:
            stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)
        if zone_id:
            stmt = stmt.where(Vehicle.zone_id == zone_id)
        if search:
            stmt = stmt.where(Vehicle.registration_number.ilike(f"%{search.replace(' ', '').upper()}%"))
        if min_capacity:
            stmt = stmt.where(Vehicle.capacity_kg >= min_capacity)
        return stmt.order_by(Vehicle.registration_number)
