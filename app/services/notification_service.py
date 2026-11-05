from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.pagination import PageParams, paginate
from app.enums import NotificationStatus, NotificationType, UserRole
from app.models import Notification, User
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def notify(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        *,
        user_id: int | None = None,
        role: UserRole | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> Notification:
        """Queue a notification (committed by the caller's transaction).

        Provide `user_id` for a direct recipient and/or `role` to broadcast to everyone holding that role.
        """
        return self.repo.add(
            Notification(
                user_id=user_id,
                target_role=role,
                notification_type=notification_type,
                title=title,
                message=message,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )

    def notify_management(self, notification_type, title, message, entity_type=None, entity_id=None):
        for role in (UserRole.OPERATIONS_MANAGER, UserRole.SUPER_ADMIN):
            self.notify(notification_type, title, message, role=role, entity_type=entity_type, entity_id=entity_id)

    # ---- reads ----
    def list_for(self, user: User, params: PageParams, status: NotificationStatus | None = None):
        return paginate(self.db, self.repo.for_user(user.id, user.role, status), params)

    def unread_count(self, user: User) -> int:
        return self.repo.count(self.repo.for_user(user.id, user.role, NotificationStatus.UNREAD))

    def mark_read(self, user: User, notification_id: int) -> Notification:
        n = self.db.get(Notification, notification_id)
        if not n or (n.user_id != user.id and n.target_role != user.role):
            raise NotFoundError("Notification not found")
        n.status = NotificationStatus.READ
        self.db.commit()
        return n

    def mark_all_read(self, user: User) -> None:
        self.repo.mark_all_read(user.id, user.role)
        self.db.commit()
