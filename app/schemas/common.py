from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.pagination import Page  # noqa: F401  (re-export)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Timestamps(ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class DateRange(BaseModel):
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def _check(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self


PositiveKg = Field(gt=0, description="Quantity in kilograms")
NonNegativeKg = Field(ge=0, description="Quantity in kilograms")
