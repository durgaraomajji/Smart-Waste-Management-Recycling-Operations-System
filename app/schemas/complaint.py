from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import ComplaintCategory, ComplaintStatus, Priority
from app.schemas.common import ORMModel


class ComplaintCreate(BaseModel):
    customer_id: int | None = None
    pickup_request_id: int | None = None
    category: ComplaintCategory
    description: str = Field(min_length=10)
    priority: Priority = Priority.MEDIUM


class ComplaintAssign(BaseModel):
    assigned_team: str = Field(min_length=2, max_length=100)
    assigned_to_id: int | None = None


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus
    remarks: str | None = None


class ComplaintOut(ORMModel):
    id: int
    complaint_no: str
    customer_id: int
    pickup_request_id: int | None
    category: ComplaintCategory
    description: str
    priority: Priority
    status: ComplaintStatus
    assigned_team: str | None
    assigned_to_id: int | None
    resolution_remarks: str | None
    created_at: datetime


class ComplaintHistoryOut(ORMModel):
    id: int
    complaint_id: int
    old_status: str | None
    new_status: str
    remarks: str | None
    changed_by_id: int | None
    created_at: datetime
