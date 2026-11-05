from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base_model import BaseModel


class SegregationRule(Base, BaseModel):
    __tablename__ = "segregation_rules"

    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    container_color: Mapped[str | None] = mapped_column(String(30), nullable=True)

    category = relationship("WasteCategory", back_populates="segregation_rules")
