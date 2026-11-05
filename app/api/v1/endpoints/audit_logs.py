from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import MANAGEMENT
from app.database.session import get_db
from app.dependencies import require_roles
from app.models import User
from app.schemas.audit_log import AuditLogOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=Page[AuditLogOut])
def list_logs(
    params: PageParams = Depends(),
    actor_id: int | None = None,
    action: str | None = None,
    entity: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_roles(*MANAGEMENT)),
    db: Session = Depends(get_db),
):
    return AuditService(db).list(params, actor_id=actor_id, action=action, entity=entity, date_from=date_from, date_to=date_to)
