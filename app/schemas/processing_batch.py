from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.enums import ProcessingStatus
from app.schemas.common import ORMModel


class BatchCreate(BaseModel):
    center_id: int
    waste_category_id: int
    input_quantity_kg: float = Field(gt=0)
    processing_date: date


class BatchComplete(BaseModel):
    recycled_output_kg: float = Field(ge=0)
    processing_loss_kg: float = Field(ge=0)

    @model_validator(mode="after")
    def _nonneg(self):
        return self


class BatchStatusUpdate(BaseModel):
    status: ProcessingStatus


class BatchOut(ORMModel):
    id: int
    batch_no: str
    center_id: int
    waste_category_id: int
    input_quantity_kg: float
    recycled_output_kg: float
    processing_loss_kg: float
    yield_percentage: float
    processing_date: date
    status: ProcessingStatus
    created_at: datetime
