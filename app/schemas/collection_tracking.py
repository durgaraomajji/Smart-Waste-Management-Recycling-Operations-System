from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.enums import CollectionStatus
from app.schemas.common import ORMModel


class CollectionStart(BaseModel):
    assignment_id: int
    remarks: str | None = None


class CollectionComplete(BaseModel):
    collected_quantity_kg: float = Field(gt=0)
    remarks: str | None = None
    photo_urls: list[HttpUrl] = []


class CollectionIncomplete(BaseModel):
    collected_quantity_kg: float = Field(default=0, ge=0)
    reason: str = Field(min_length=3)
    photo_urls: list[HttpUrl] = []
    missed: bool = False  # True = nothing was collected (counts as a missed pickup)


class CollectionOut(ORMModel):
    id: int
    assignment_id: int
    pickup_request_id: int
    status: CollectionStatus
    started_at: datetime | None
    completed_at: datetime | None
    collected_quantity_kg: float | None
    remarks: str | None
    photo_urls: list[str] | None
    incomplete_reason: str | None
