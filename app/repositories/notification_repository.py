from sqlalchemy import or_, select, update

from app.enums import NotificationStatus, UserRole
from app.models import Notification
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def select(self):
        return select(Notification)

    def for_user(self, user_id: int, role: UserRole, status: NotificationStatus | None = None):
        stmt = select(Notification).where(or_(Notification.user_id == user_id, Notification.target_role == role))
        if status:
            stmt = stmt.where(Notification.status == status)
        return stmt.order_by(Notification.id.desc())

    def mark_all_read(self, user_id: int, role: UserRole) -> None:
        self.db.execute(
            update(Notification)
            .where(or_(Notification.user_id == user_id, Notification.target_role == role), Notification.status == NotificationStatus.UNREAD)
            .values(status=NotificationStatus.READ)
        )

    def exists_unread(self, notification_type, entity_type: str, entity_id: int) -> bool:
        """Used by background tasks to avoid duplicate alerts."""
        return self.count(
            select(Notification).where(
                Notification.notification_type == notification_type,
                Notification.entity_type == entity_type,
                Notification.entity_id == entity_id,
                Notification.status == NotificationStatus.UNREAD,
            )
        ) > 0
