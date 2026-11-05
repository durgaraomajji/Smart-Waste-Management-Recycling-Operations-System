from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import BaseModel


class VehicleMaintenance(Base, BaseModel):
    """Completed maintenance record (history) per vehicle - written when a maintenance request completes."""
    __tablename__ = "vehicle_maintenance"

    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True, nullable=False)
    maintenance_request_id: Mapped[int | None] = mapped_column(ForeignKey("maintenance_requests.id"), nullable=True)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    performed_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    odometer_km: Mapped[float | None] = mapped_column(Float, nullable=True)
