from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import BaseModel


class WasteSegregation(Base, BaseModel):
    __tablename__ = "waste_segregations"

    transfer_id: Mapped[int | None] = mapped_column(ForeignKey("waste_transfers.id"), index=True, nullable=True)
    center_id: Mapped[int] = mapped_column(ForeignKey("recycling_centers.id"), index=True, nullable=False)
    waste_category_id: Mapped[int] = mapped_column(ForeignKey("waste_categories.id"), index=True, nullable=False)
    incoming_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    recyclable_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    non_recyclable_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    contaminated_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recorded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
