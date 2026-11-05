from datetime import date

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import ALL_ROLES, SUPERVISION
from app.database.session import get_db
from app.dependencies import client_ip, get_current_user, require_roles
from app.enums import PickupStatus, Priority
from app.models import User
from app.core.responses import MessageResponse
from app.schemas.pickup_request import PickupCancel, PickupCreate, PickupOut, PickupStatusUpdate
from app.services.pickup_service import PickupService

router = APIRouter(prefix="/pickup-requests", tags=["Pickup Requests"])


@router.post("", response_model=PickupOut, status_code=status.HTTP_201_CREATED)
def create_pickup(data: PickupCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return PickupService(db).create(user, data, client_ip(request))


@router.get("", response_model=Page[PickupOut])
def list_pickups(
    params: PageParams = Depends(),
    status: PickupStatus | None = None,
    priority: Priority | None = None,
    customer_id: int | None = None,
    zone_id: int | None = None,
    waste_category_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PickupService(db).list(
        user,
        params,
        status=status,
        priority=priority,
        customer_id=customer_id,
        zone_id=zone_id,
        waste_category_id=waste_category_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{pickup_id}", response_model=PickupOut)
def get_pickup(pickup_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return PickupService(db).get(pickup_id, user)


@router.patch("/{pickup_id}/status", response_model=PickupOut, summary="Approve or reject a request")
def change_status(pickup_id: int, data: PickupStatusUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return PickupService(db).change_status(actor, pickup_id, data.status, data.reason)


@router.post("/{pickup_id}/cancel", response_model=PickupOut, summary="Cancel a request")
def cancel_pickup(pickup_id: int, data: PickupCancel, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return PickupService(db).cancel(user, pickup_id, data.reason)


@router.delete("/{pickup_id}", response_model=MessageResponse)
def delete_pickup(pickup_id: int, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    PickupService(db).delete(actor, pickup_id)
    return {"message": "Pickup request deleted"}
