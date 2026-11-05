from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import CollectionStatus
from app.models.base_model import BaseModel, EnumType


class CollectionRecord(Base, BaseModel):
    __tablename__ = "collection_records"

    assignment_id: Mapped[int] = mapped_column(ForeignKey("collection_assignments.id"), index=True, nullable=False)
    pickup_request_id: Mapped[int] = mapped_column(ForeignKey("pickup_requests.id"), index=True, nullable=False)
    status: Mapped[CollectionStatus] = mapped_column(EnumType(CollectionStatus), default=CollectionStatus.STARTED, nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    collected_quantity_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    incomplete_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
