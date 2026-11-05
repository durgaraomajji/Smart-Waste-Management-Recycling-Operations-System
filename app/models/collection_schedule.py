from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import BaseModel


class CollectionSchedule(Base, BaseModel):
    __tablename__ = "collection_schedules"

    zone_id: Mapped[int] = mapped_column(ForeignKey("service_zones.id"), index=True, nullable=False)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("collection_areas.id"), nullable=True)
    waste_category_id: Mapped[int | None] = mapped_column(ForeignKey("waste_categories.id"), nullable=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = Monday ... 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), default="weekly", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
