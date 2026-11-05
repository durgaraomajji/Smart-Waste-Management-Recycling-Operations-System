from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import FuelType, VehicleStatus, VehicleType
from app.models.base_model import BaseModel, EnumType


class Vehicle(Base, BaseModel):
    __tablename__ = "vehicles"

    registration_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(EnumType(VehicleType), nullable=False)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(EnumType(FuelType), nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(EnumType(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False, index=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("service_zones.id"), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
