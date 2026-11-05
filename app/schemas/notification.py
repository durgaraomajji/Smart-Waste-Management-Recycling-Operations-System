from datetime import datetime

from app.enums import NotificationStatus, NotificationType
from app.schemas.common import ORMModel


class NotificationOut(ORMModel):
    id: int
    notification_type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    entity_type: str | None
    entity_id: int | None
    created_at: datetime
