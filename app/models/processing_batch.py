from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import ProcessingStatus
from app.models.base_model import BaseModel, EnumType


class ProcessingBatch(Base, BaseModel):
    __tablename__ = "processing_batches"

    batch_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    center_id: Mapped[int] = mapped_column(ForeignKey("recycling_centers.id"), index=True, nullable=False)
    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
    input_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    recycled_output_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    processing_loss_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    yield_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    processing_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(EnumType(ProcessingStatus), default=ProcessingStatus.PLANNED, nullable=False, index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
