from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import ZoneStatus
from app.models.base_model import BaseModel, EnumType


class CollectionArea(Base, BaseModel):
    __tablename__ = "collection_areas"
    __table_args__ = (UniqueConstraint("zone_id", "name", name="uq_area_zone_name"),)

    zone_id: Mapped[int] = mapped_column(ForeignKey("service_zones.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[ZoneStatus] = mapped_column(EnumType(ZoneStatus), default=ZoneStatus.ACTIVE, nullable=False)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    zone = relationship("ServiceZone", back_populates="areas")
    streets = relationship("Street", back_populates="area", lazy="selectin")
