from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import DisposalMethod, DisposalStatus
from app.models.base_model import BaseModel, EnumType


class DisposalRecord(Base, BaseModel):
    __tablename__ = "disposal_records"

    disposal_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    center_id: Mapped[int | None] = mapped_column(ForeignKey("recycling_centers.id"), index=True, nullable=True)
    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
    method: Mapped[DisposalMethod] = mapped_column(EnumType(DisposalMethod), nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    disposal_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    responsible_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[DisposalStatus] = mapped_column(EnumType(DisposalStatus), default=DisposalStatus.PENDING_APPROVAL, nullable=False, index=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
