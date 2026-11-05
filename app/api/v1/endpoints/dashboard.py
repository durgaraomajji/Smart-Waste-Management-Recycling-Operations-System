from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import MANAGEMENT
from app.database.session import get_db
from app.dependencies import require_roles
from app.models import User
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(_: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return DashboardService(db).summary()
