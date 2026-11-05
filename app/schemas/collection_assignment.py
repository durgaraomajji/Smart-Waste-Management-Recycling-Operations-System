from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import AssignmentStatus
from app.schemas.common import ORMModel
from app.schemas.workforce import WorkerOut


class AssignmentCreate(BaseModel):
    pickup_request_id: int
    driver_id: int
    vehicle_id: int
    worker_ids: list[int] = Field(default_factory=list)
    scheduled_at: datetime
    remarks: str | None = None


class AssignmentReassign(BaseModel):
    driver_id: int | None = None
    vehicle_id: int | None = None
    worker_ids: list[int] | None = None
    scheduled_at: datetime | None = None
    remarks: str | None = None


class AssignmentOut(ORMModel):
    id: int
    pickup_request_id: int
    driver_id: int
    vehicle_id: int
    scheduled_at: datetime
    status: AssignmentStatus
    remarks: str | None
    workers: list[WorkerOut] = []


class AssignmentHistoryOut(ORMModel):
    id: int
    assignment_id: int
    action: str
    old_values: dict | None
    new_values: dict | None
    changed_by_id: int | None
    remarks: str | None
    created_at: datetime


class ScheduleSet(BaseModel):
    """Confirm / change the collection slot. Moves the pickup from 'assigned' to 'scheduled'."""
    scheduled_at: datetime
