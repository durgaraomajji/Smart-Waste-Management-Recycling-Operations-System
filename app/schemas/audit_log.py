from datetime import datetime

from app.schemas.common import ORMModel


class AuditLogOut(ORMModel):
    id: int
    actor_id: int | None
    actor_email: str | None
    action: str
    entity: str
    entity_id: int | None
    details: dict | None
    ip_address: str | None
    created_at: datetime
