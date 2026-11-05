from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.enums import FuelType, VehicleStatus, VehicleType
from app.schemas.common import ORMModel


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=4, max_length=30)
    vehicle_type: VehicleType
    capacity_kg: float = Field(gt=0)
    fuel_type: FuelType
    zone_id: int | None = None
    purchase_date: date | None = None

    @field_validator("registration_number")
    @classmethod
    def _norm(cls, v: str):
        return v.replace(" ", "").upper()


class VehicleUpdate(BaseModel):
    capacity_kg: float | None = Field(default=None, gt=0)
    zone_id: int | None = None
    fuel_type: FuelType | None = None


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus


class VehicleOut(ORMModel):
    id: int
    registration_number: str
    vehicle_type: VehicleType
    capacity_kg: float
    fuel_type: FuelType
    status: VehicleStatus
    zone_id: int | None
    last_service_date: date | None
    next_service_date: date | None


class VehicleMaintenanceOut(ORMModel):
    id: int
    vehicle_id: int
    maintenance_request_id: int | None
    service_date: date
    description: str
    cost: float
    performed_by: str | None
    odometer_km: float | None


class AvailabilityOut(ORMModel):
    vehicle_id: int
    registration_number: str
    available: bool
    reason: str | None = None
