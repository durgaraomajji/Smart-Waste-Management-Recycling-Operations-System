from datetime import date

from sqlalchemy import select

from app.models import AuditLog
from app.repositories.base_repository import BaseRepository, day_end, day_start


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def select(self):
        return select(AuditLog)

    def filtered(
        self,
        actor_id: int | None = None,
        action: str | None = None,
        entity: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        stmt = select(AuditLog)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity:
            stmt = stmt.where(AuditLog.entity == entity)
        if date_from:
            stmt = stmt.where(AuditLog.created_at >= day_start(date_from))
        if date_to:
            stmt = stmt.where(AuditLog.created_at <= day_end(date_to))
        return stmt.order_by(AuditLog.id.desc())
