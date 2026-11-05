from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import ComplaintCategory, ComplaintStatus, Priority
from app.models.base_model import BaseModel, EnumType


class Complaint(Base, BaseModel):
    __tablename__ = "complaints"

    complaint_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    pickup_request_id: Mapped[int | None] = mapped_column(ForeignKey("pickup_requests.id"), nullable=True)
    category: Mapped[ComplaintCategory] = mapped_column(EnumType(ComplaintCategory), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(EnumType(Priority), default=Priority.MEDIUM, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(EnumType(ComplaintStatus), default=ComplaintStatus.OPEN, nullable=False, index=True)
    assigned_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolution_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
