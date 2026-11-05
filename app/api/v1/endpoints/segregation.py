from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import CENTER_STAFF
from app.database.session import get_db
from app.dependencies import require_roles
from app.models import User
from app.schemas.waste_segregation import SegregationCreate, SegregationOut
from app.services.segregation_service import SegregationService

router = APIRouter(prefix="/segregation", tags=["Waste Segregation"])


@router.post("", response_model=SegregationOut, status_code=status.HTTP_201_CREATED)
def record(data: SegregationCreate, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return SegregationService(db).create(actor, data)


@router.get("", response_model=Page[SegregationOut], summary="Segregation history")
def history(
    params: PageParams = Depends(),
    center_id: int | None = None,
    waste_category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_roles(*CENTER_STAFF)),
    db: Session = Depends(get_db),
):
    return SegregationService(db).list(params, center_id=center_id, waste_category_id=waste_category_id, date_from=date_from, date_to=date_to)


@router.get("/{record_id}", response_model=SegregationOut)
def get_record(record_id: int, _: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return SegregationService(db).get(record_id)
