from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base_model import BaseModel


class CustomerAddress(Base, BaseModel):
    __tablename__ = "customer_addresses"

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(50), default="home", nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    street_id: Mapped[int | None] = mapped_column(ForeignKey("streets.id"), nullable=True)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("collection_areas.id"), nullable=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("service_zones.id"), index=True, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)   # customer location mapping
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer = relationship("Customer", back_populates="addresses")
