from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


class SegregationCreate(BaseModel):
    transfer_id: int | None = None
    center_id: int
    waste_category_id: int
    incoming_quantity_kg: float = Field(gt=0)
    recyclable_kg: float = Field(ge=0)
    non_recyclable_kg: float = Field(ge=0)
    contaminated_kg: float = Field(default=0, ge=0)
    remarks: str | None = None

    @model_validator(mode="after")
    def _balance(self):
        total = self.recyclable_kg + self.non_recyclable_kg + self.contaminated_kg
        if total > self.incoming_quantity_kg + 1e-6:
            raise ValueError("recyclable + non-recyclable + contaminated cannot exceed incoming quantity")
        return self


class SegregationOut(ORMModel):
    id: int
    transfer_id: int | None
    center_id: int
    waste_category_id: int
    incoming_quantity_kg: float
    recyclable_kg: float
    non_recyclable_kg: float
    contaminated_kg: float
    remarks: str | None
    created_at: datetime
