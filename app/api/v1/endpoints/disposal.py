from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import CENTER_STAFF, MANAGEMENT
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import DisposalMethod, DisposalStatus
from app.models import User
from app.schemas.disposal import DisposalCreate, DisposalDecision, DisposalOut
from app.services.disposal_service import DisposalService

router = APIRouter(prefix="/disposals", tags=["Disposal"])


@router.post("", response_model=DisposalOut, status_code=status.HTTP_201_CREATED)
def create_disposal(data: DisposalCreate, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return DisposalService(db).create(actor, data)


@router.get("", response_model=Page[DisposalOut], summary="Disposal history")
def list_disposals(
    params: PageParams = Depends(),
    status: DisposalStatus | None = None,
    method: DisposalMethod | None = None,
    waste_category_id: int | None = None,
    center_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_roles(*CENTER_STAFF)),
    db: Session = Depends(get_db),
):
    return DisposalService(db).list(
        params, status=status, method=method, waste_category_id=waste_category_id,
        center_id=center_id, date_from=date_from, date_to=date_to,
    )


@router.get("/{disposal_id}", response_model=DisposalOut)
def get_disposal(disposal_id: int, _: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return DisposalService(db).get(disposal_id)


@router.post("/{disposal_id}/decision", response_model=DisposalOut, summary="Approve or reject a disposal")
def decide(disposal_id: int, data: DisposalDecision, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return DisposalService(db).decide(actor, disposal_id, data.approve, data.remarks)


@router.post("/{disposal_id}/complete", response_model=DisposalOut, summary="Mark an approved disposal as carried out")
def mark_disposed(disposal_id: int, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return DisposalService(db).mark_disposed(actor, disposal_id)
