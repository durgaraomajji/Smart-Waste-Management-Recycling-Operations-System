from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import WorkforceStatus
from app.models.base_model import BaseModel, EnumType


class Driver(Base, BaseModel):
    __tablename__ = "drivers"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    license_class: Mapped[str | None] = mapped_column(String(20), nullable=True)
    skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[WorkforceStatus] = mapped_column(EnumType(WorkforceStatus), default=WorkforceStatus.AVAILABLE, nullable=False, index=True)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
