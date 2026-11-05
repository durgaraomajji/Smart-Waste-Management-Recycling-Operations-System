from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base_model import IDMixin, TimestampMixin


class AuditLog(Base, IDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    entity: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
