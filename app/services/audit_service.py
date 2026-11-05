from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, User
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Writes audit entries inside the caller's transaction (no commit here)."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def log(
        self,
        actor: User | None,
        action: str,
        entity: str,
        entity_id: int | None = None,
        details: dict[str, Any] | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        return self.repo.add(
            AuditLog(
                actor_id=actor.id if actor else None,
                actor_email=actor.email if actor else None,
                action=action,
                entity=entity,
                entity_id=entity_id,
                details=details,
                ip_address=ip,
            )
        )

    def list(self, params, **filters):
        from app.core.pagination import paginate

        return paginate(self.db, self.repo.filtered(**filters), params)
