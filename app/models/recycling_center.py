from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import CenterStatus
from app.models.base_model import BaseModel, EnumType


class RecyclingCenter(Base, BaseModel):
    __tablename__ = "recycling_centers"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("service_zones.id"), nullable=True)
    daily_capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    current_load_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[CenterStatus] = mapped_column(EnumType(CenterStatus), default=CenterStatus.ACTIVE, nullable=False, index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)

    accepted_categories = relationship("CenterWasteCategory", lazy="selectin", cascade="all, delete-orphan")
