from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums import ZoneStatus
from app.models.base_model import BaseModel, EnumType


class Customer(Base, BaseModel):
    __tablename__ = "customers"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    customer_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("service_zones.id"), index=True, nullable=True)
    # service status reuses ZoneStatus semantic: active / inactive / suspended
    service_status: Mapped[ZoneStatus] = mapped_column(EnumType(ZoneStatus), default=ZoneStatus.ACTIVE, nullable=False, index=True)

    addresses = relationship("CustomerAddress", back_populates="customer", lazy="selectin")
