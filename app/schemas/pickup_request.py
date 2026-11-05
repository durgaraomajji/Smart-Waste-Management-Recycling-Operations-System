from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.enums import PickupStatus, Priority
from app.schemas.common import ORMModel


class PickupCreate(BaseModel):
    customer_id: int | None = None  # staff may create on behalf of a customer; customers omit it
    address_id: int
    waste_category_id: int
    estimated_quantity_kg: float = Field(gt=0, le=100000)
    preferred_date: date
    priority: Priority = Priority.MEDIUM
    notes: str | None = None

    @field_validator("preferred_date")
    @classmethod
    def _not_past(cls, v: date):
        if v < date.today():
            raise ValueError("preferred_date cannot be in the past")
        return v


class PickupStatusUpdate(BaseModel):
    status: PickupStatus
    reason: str | None = None


class PickupCancel(BaseModel):
    reason: str = Field(min_length=3)


class PickupOut(ORMModel):
    id: int
    request_no: str
    customer_id: int
    address_id: int
    zone_id: int | None
    waste_category_id: int
    estimated_quantity_kg: float
    preferred_date: date
    priority: Priority
    status: PickupStatus
    notes: str | None
    status_reason: str | None
    created_at: datetime
