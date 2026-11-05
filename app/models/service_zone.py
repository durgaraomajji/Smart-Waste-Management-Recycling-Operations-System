from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import ZoneStatus
from app.models.base_model import BaseModel, EnumType


class ServiceZone(Base, BaseModel):
    __tablename__ = "service_zones"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ZoneStatus] = mapped_column(EnumType(ZoneStatus), default=ZoneStatus.ACTIVE, nullable=False, index=True)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)

    areas = relationship("CollectionArea", back_populates="zone", lazy="selectin")
