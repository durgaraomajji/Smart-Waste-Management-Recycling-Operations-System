from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import TransferStatus
from app.models.base_model import BaseModel, EnumType


class WasteTransfer(Base, BaseModel):
    __tablename__ = "waste_transfers"

    transfer_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    source_zone_id: Mapped[int] = mapped_column(ForeignKey("service_zones.id"), index=True, nullable=False)
    center_id: Mapped[int] = mapped_column(ForeignKey("recycling_centers.id"), index=True, nullable=False)
    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    status: Mapped[TransferStatus] = mapped_column(EnumType(TransferStatus), default=TransferStatus.PENDING, nullable=False, index=True)
    initiated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
