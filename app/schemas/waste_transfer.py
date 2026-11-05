from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import TransferStatus
from app.schemas.common import ORMModel


class TransferCreate(BaseModel):
    source_zone_id: int
    center_id: int
    waste_category_id: int
    quantity_kg: float = Field(gt=0)
    vehicle_id: int
    remarks: str | None = None


class TransferStatusUpdate(BaseModel):
    status: TransferStatus
    remarks: str | None = None


class TransferOut(ORMModel):
    id: int
    transfer_no: str
    source_zone_id: int
    center_id: int
    waste_category_id: int
    quantity_kg: float
    vehicle_id: int
    status: TransferStatus
    dispatched_at: datetime | None
    delivered_at: datetime | None
    remarks: str | None
    created_at: datetime
