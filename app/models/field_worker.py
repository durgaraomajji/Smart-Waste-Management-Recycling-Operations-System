from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import WorkforceStatus
from app.models.base_model import BaseModel, EnumType


class FieldWorker(Base, BaseModel):
    __tablename__ = "field_workers"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[WorkforceStatus] = mapped_column(EnumType(WorkforceStatus), default=WorkforceStatus.AVAILABLE, nullable=False, index=True)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
