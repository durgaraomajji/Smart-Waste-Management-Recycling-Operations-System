from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import NotificationStatus, NotificationType, UserRole
from app.models.base_model import IDMixin, TimestampMixin, EnumType


class Notification(Base, IDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)  # direct recipient
    target_role: Mapped[UserRole | None] = mapped_column(EnumType(UserRole), index=True, nullable=True)  # role broadcast
    notification_type: Mapped[NotificationType] = mapped_column(EnumType(NotificationType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(EnumType(NotificationStatus), default=NotificationStatus.UNREAD, nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
