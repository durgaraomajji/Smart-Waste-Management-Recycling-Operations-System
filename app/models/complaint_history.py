from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import IDMixin, TimestampMixin


class ComplaintHistory(Base, IDMixin, TimestampMixin):
    __tablename__ = "complaint_history"

    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True, nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
