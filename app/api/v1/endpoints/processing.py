from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import CENTER_STAFF
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import ProcessingStatus
from app.models import User
from app.schemas.processing_batch import BatchComplete, BatchCreate, BatchOut
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/processing", tags=["Recycling Processing"])


@router.post("/batches", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(data: BatchCreate, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return ProcessingService(db).create(actor, data)


@router.get("/batches", response_model=Page[BatchOut])
def list_batches(
    params: PageParams = Depends(),
    status: ProcessingStatus | None = None,
    center_id: int | None = None,
    waste_category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_roles(*CENTER_STAFF)),
    db: Session = Depends(get_db),
):
    return ProcessingService(db).list(params, status=status, center_id=center_id, waste_category_id=waste_category_id, date_from=date_from, date_to=date_to)


@router.get("/batches/{batch_id}", response_model=BatchOut)
def get_batch(batch_id: int, _: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return ProcessingService(db).get(batch_id)


@router.post("/batches/{batch_id}/start", response_model=BatchOut)
def start_batch(batch_id: int, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return ProcessingService(db).start(actor, batch_id)


@router.post("/batches/{batch_id}/complete", response_model=BatchOut, summary="Record output / loss; yield % is calculated")
def complete_batch(batch_id: int, data: BatchComplete, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return ProcessingService(db).complete(actor, batch_id, data)


@router.post("/batches/{batch_id}/fail", response_model=BatchOut)
def fail_batch(batch_id: int, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return ProcessingService(db).fail(actor, batch_id)
