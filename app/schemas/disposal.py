from datetime import date, datetime

from pydantic import BaseModel, Field

from app.enums import DisposalMethod, DisposalStatus
from app.schemas.common import ORMModel


class DisposalCreate(BaseModel):
    center_id: int | None = None
    waste_category_id: int
    method: DisposalMethod
    quantity_kg: float = Field(gt=0)
    location: str = Field(min_length=3, max_length=255)
    disposal_date: date
    responsible_user_id: int | None = None
    remarks: str | None = None


class DisposalDecision(BaseModel):
    approve: bool
    remarks: str | None = None


class DisposalOut(ORMModel):
    id: int
    disposal_no: str
    center_id: int | None
    waste_category_id: int
    method: DisposalMethod
    quantity_kg: float
    location: str
    disposal_date: date
    responsible_user_id: int
    status: DisposalStatus
    approved_by_id: int | None
    approved_at: datetime | None
    remarks: str | None
