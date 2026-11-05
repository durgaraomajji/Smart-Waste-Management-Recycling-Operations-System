from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import RecyclabilityStatus
from app.models.base_model import BaseModel, EnumType


class WasteCategory(Base, BaseModel):
    __tablename__ = "waste_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(60), nullable=True)  # e.g. biodegradable / dry / e-waste
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recyclability: Mapped[RecyclabilityStatus] = mapped_column(
        EnumType(RecyclabilityStatus), default=RecyclabilityStatus.RECYCLABLE, nullable=False
    )
    disposal_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    segregation_rules = relationship("SegregationRule", back_populates="category", lazy="selectin")
