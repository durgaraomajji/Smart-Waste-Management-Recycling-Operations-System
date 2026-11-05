from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import CENTER_STAFF, SUPERVISION
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import TransferStatus
from app.models import User
from app.schemas.waste_transfer import TransferCreate, TransferOut, TransferStatusUpdate
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["Waste Transfers"])


@router.post("", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
def create_transfer(data: TransferCreate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return TransferService(db).create(actor, data)


@router.get("", response_model=Page[TransferOut], summary="Transfer history")
def list_transfers(
    params: PageParams = Depends(),
    status: TransferStatus | None = None,
    center_id: int | None = None,
    source_zone_id: int | None = None,
    waste_category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_roles(*SUPERVISION, *CENTER_STAFF)),
    db: Session = Depends(get_db),
):
    return TransferService(db).list(
        params, status=status, center_id=center_id, source_zone_id=source_zone_id,
        waste_category_id=waste_category_id, date_from=date_from, date_to=date_to,
    )


@router.get("/stock", summary="Collected waste in a zone not yet transferred")
def available_stock(zone_id: int, waste_category_id: int, _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return {"zone_id": zone_id, "waste_category_id": waste_category_id, "available_kg": TransferService(db).available_stock_kg(zone_id, waste_category_id)}


@router.get("/{transfer_id}", response_model=TransferOut)
def get_transfer(transfer_id: int, _: User = Depends(require_roles(*SUPERVISION, *CENTER_STAFF)), db: Session = Depends(get_db)):
    return TransferService(db).get(transfer_id)


@router.patch("/{transfer_id}/status", response_model=TransferOut)
def update_status(transfer_id: int, data: TransferStatusUpdate, actor: User = Depends(require_roles(*SUPERVISION, *CENTER_STAFF)), db: Session = Depends(get_db)):
    return TransferService(db).update_status(actor, transfer_id, data.status, data.remarks)
