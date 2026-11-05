from datetime import date, datetime

from pydantic import BaseModel, Field

from app.enums import MaintenanceStatus, MaintenanceType, Priority
from app.schemas.common import ORMModel


class MaintenanceRequestCreate(BaseModel):
    vehicle_id: int
    maintenance_type: MaintenanceType = MaintenanceType.CORRECTIVE
    description: str = Field(min_length=3)
    priority: Priority = Priority.MEDIUM
    scheduled_date: date | None = None


class BreakdownReport(BaseModel):
    vehicle_id: int
    description: str = Field(min_length=3)


class TechnicianAssign(BaseModel):
    technician_id: int
    scheduled_date: date | None = None


class MaintenanceComplete(BaseModel):
    cost: float = Field(ge=0)
    performed_by: str | None = None
    odometer_km: float | None = Field(default=None, ge=0)
    notes: str | None = None


class MaintenanceRequestOut(ORMModel):
    id: int
    vehicle_id: int
    maintenance_type: MaintenanceType
    description: str
    priority: Priority
    status: MaintenanceStatus
    reported_by_id: int | None
    technician_id: int | None
    scheduled_date: date | None
    started_at: datetime | None
    completed_at: datetime | None
    cost: float
    downtime_hours: float


class ScheduleCreate(BaseModel):
    vehicle_id: int
    description: str = Field(min_length=3)
    interval_days: int = Field(gt=0, le=730)
    last_service_date: date | None = None


class MaintenanceScheduleOut(ORMModel):
    id: int
    vehicle_id: int
    description: str
    interval_days: int
    last_service_date: date | None
    next_due_date: date
    is_active: bool
