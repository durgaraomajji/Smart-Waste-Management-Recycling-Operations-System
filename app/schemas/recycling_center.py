from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import CenterStatus
from app.schemas.common import ORMModel


class CenterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)
    address: str = Field(min_length=3, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    zone_id: int | None = None
    daily_capacity_kg: float = Field(gt=0)
    manager_id: int | None = None
    accepted_category_ids: list[int] = []


class CenterUpdate(BaseModel):
    address: str | None = None
    daily_capacity_kg: float | None = Field(default=None, gt=0)
    latitude: float | None = None
    longitude: float | None = None


class CenterStatusUpdate(BaseModel):
    status: CenterStatus


class AssignManager(BaseModel):
    manager_id: int


class AcceptedCategories(BaseModel):
    category_ids: list[int]


class CenterOut(ORMModel):
    id: int
    name: str
    code: str
    address: str
    latitude: float | None
    longitude: float | None
    zone_id: int | None
    daily_capacity_kg: float
    current_load_kg: float
    status: CenterStatus
    manager_id: int | None
    accepted_category_ids: list[int] = []
    created_at: datetime


class CenterAvailability(ORMModel):
    center_id: int
    status: CenterStatus
    daily_capacity_kg: float
    current_load_kg: float
    available_capacity_kg: float
    utilization_pct: float
