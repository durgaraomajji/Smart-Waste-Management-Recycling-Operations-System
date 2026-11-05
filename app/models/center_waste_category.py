from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import IDMixin


class CenterWasteCategory(Base, IDMixin):
    __tablename__ = "center_waste_categories"
    __table_args__ = (UniqueConstraint("center_id", "waste_category_id", name="uq_center_category"),)

    center_id: Mapped[int] = mapped_column(ForeignKey("recycling_centers.id"), index=True, nullable=False)
    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
