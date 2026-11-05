from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import BaseModel


class MaintenanceSchedule(Base, BaseModel):
    __tablename__ = "maintenance_schedules"

    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    last_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
