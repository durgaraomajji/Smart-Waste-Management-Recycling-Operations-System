from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base_model import BaseModel


class Street(Base, BaseModel):
    __tablename__ = "streets"
    __table_args__ = (UniqueConstraint("area_id", "name", "locality", name="uq_street_area_name_locality"),)

    area_id: Mapped[int] = mapped_column(ForeignKey("collection_areas.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    locality: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    area = relationship("CollectionArea", back_populates="streets")
