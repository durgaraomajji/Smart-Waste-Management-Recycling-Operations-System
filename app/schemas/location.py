from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator

from app.enums import ZoneStatus
from app.schemas.common import ORMModel


class StreetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    locality: str | None = Field(default=None, max_length=150)
    pincode: str | None = Field(default=None, max_length=10)


class StreetOut(ORMModel):
    id: int
    area_id: int
    name: str
    locality: str | None
    pincode: str | None


class AreaCreate(BaseModel):
    zone_id: int
    name: str = Field(min_length=2, max_length=120)
    supervisor_id: int | None = None


class AreaOut(ORMModel):
    id: int
    zone_id: int
    name: str
    status: ZoneStatus
    supervisor_id: int | None
    streets: list[StreetOut] = []


class ZoneCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=20)
    description: str | None = None
    supervisor_id: int | None = None


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None


class ZoneStatusUpdate(BaseModel):
    status: ZoneStatus


class AssignSupervisor(BaseModel):
    supervisor_id: int


class ZoneOut(ORMModel):
    id: int
    name: str
    code: str
    description: str | None
    status: ZoneStatus
    supervisor_id: int | None
    created_at: datetime


class ZoneDetail(ZoneOut):
    areas: list[AreaOut] = []


class ScheduleCreate(BaseModel):
    zone_id: int
    area_id: int | None = None
    waste_category_id: int | None = None
    day_of_week: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: time
    end_time: time
    frequency: str = Field(default="weekly", pattern="^(daily|weekly|biweekly|monthly)$")

    @model_validator(mode="after")
    def _times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ScheduleOut(ORMModel):
    id: int
    zone_id: int
    area_id: int | None
    waste_category_id: int | None
    day_of_week: int
    start_time: time
    end_time: time
    frequency: str
    is_active: bool
