from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import ALL_ROLES, SUPERVISION
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import CollectionStatus, UserRole
from app.models import User
from app.schemas.collection_tracking import CollectionComplete, CollectionIncomplete, CollectionOut, CollectionStart
from app.services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["Collection Tracking"])

FIELD = (UserRole.DRIVER, UserRole.FIELD_WORKER, UserRole.COLLECTION_SUPERVISOR, UserRole.OPERATIONS_MANAGER)


@router.post("/start", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def start_collection(data: CollectionStart, user: User = Depends(require_roles(*FIELD)), db: Session = Depends(get_db)):
    return CollectionService(db).start(user, data)


@router.post("/{record_id}/complete", response_model=CollectionOut, summary="Record collected quantity, remarks and photo URLs")
def complete_collection(record_id: int, data: CollectionComplete, user: User = Depends(require_roles(*FIELD)), db: Session = Depends(get_db)):
    return CollectionService(db).complete(user, record_id, data)


@router.post("/{record_id}/incomplete", response_model=CollectionOut, summary="Record an incomplete or missed pickup")
def incomplete_collection(record_id: int, data: CollectionIncomplete, user: User = Depends(require_roles(*FIELD)), db: Session = Depends(get_db)):
    return CollectionService(db).incomplete(user, record_id, data)


@router.get("", response_model=Page[CollectionOut], summary="Collection history")
def list_collections(
    params: PageParams = Depends(),
    status: CollectionStatus | None = None,
    pickup_request_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CollectionService(db).list(
        user, params, status=status, pickup_request_id=pickup_request_id, date_from=date_from, date_to=date_to
    )


@router.get("/{record_id}", response_model=CollectionOut)
def get_collection(record_id: int, _: User = Depends(require_roles(*FIELD)), db: Session = Depends(get_db)):
    return CollectionService(db).get(record_id)
