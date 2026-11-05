from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import IDMixin, TimestampMixin


class AssignmentHistory(Base, IDMixin, TimestampMixin):
    __tablename__ = "assignment_history"

    assignment_id: Mapped[int] = mapped_column(ForeignKey("collection_assignments.id"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)  # assigned / reassigned / cancelled / completed
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
