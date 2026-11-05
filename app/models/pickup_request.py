from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import PickupStatus, Priority
from app.models.base_model import BaseModel, EnumType


class PickupRequest(Base, BaseModel):
    __tablename__ = "pickup_requests"

    request_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("customer_addresses.id"), nullable=False)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("service_zones.id"), index=True, nullable=True)
    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
    estimated_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    priority: Mapped[Priority] = mapped_column(EnumType(Priority), default=Priority.MEDIUM, nullable=False, index=True)
    status: Mapped[PickupStatus] = mapped_column(EnumType(PickupStatus), default=PickupStatus.PENDING, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # reject / cancel reason
    requested_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
