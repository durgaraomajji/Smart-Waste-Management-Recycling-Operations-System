from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import MaintenanceStatus, MaintenanceType, Priority
from app.models.base_model import BaseModel, EnumType


class MaintenanceRequest(Base, BaseModel):
    __tablename__ = "maintenance_requests"

    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True, nullable=False)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(EnumType(MaintenanceType), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(EnumType(Priority), default=Priority.MEDIUM, nullable=False)
    status: Mapped[MaintenanceStatus] = mapped_column(EnumType(MaintenanceStatus), default=MaintenanceStatus.REQUESTED, nullable=False, index=True)
    reported_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
