from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import CENTER_STAFF, INTERNAL_STAFF, MANAGEMENT
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import CenterStatus
from app.models import User
from app.schemas.recycling_center import (
    AcceptedCategories,
    AssignManager,
    CenterAvailability,
    CenterCreate,
    CenterOut,
    CenterStatusUpdate,
    CenterUpdate,
)
from app.services.recycling_center_service import RecyclingCenterService

router = APIRouter(prefix="/recycling-centers", tags=["Recycling Centers"])


def _out(center) -> dict:
    return {
        **{c.name: getattr(center, c.name) for c in center.__table__.columns},
        "accepted_category_ids": sorted(a.waste_category_id for a in center.accepted_categories),
    }


@router.post("", response_model=CenterOut, status_code=status.HTTP_201_CREATED)
def create_center(data: CenterCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return _out(RecyclingCenterService(db).create(actor, data))


@router.get("", response_model=Page[CenterOut])
def list_centers(
    params: PageParams = Depends(),
    status: CenterStatus | None = None,
    zone_id: int | None = None,
    search: str | None = None,
    category_id: int | None = None,
    _: User = Depends(require_roles(*INTERNAL_STAFF)),
    db: Session = Depends(get_db),
):
    page = RecyclingCenterService(db).list(params, status=status, zone_id=zone_id, search=search, category_id=category_id)
    page["items"] = [_out(c) for c in page["items"]]
    return page


@router.get("/{center_id}", response_model=CenterOut)
def get_center(center_id: int, _: User = Depends(require_roles(*INTERNAL_STAFF)), db: Session = Depends(get_db)):
    return _out(RecyclingCenterService(db).get(center_id))


@router.patch("/{center_id}", response_model=CenterOut)
def update_center(center_id: int, data: CenterUpdate, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return _out(RecyclingCenterService(db).update(actor, center_id, data))


@router.patch("/{center_id}/status", response_model=CenterOut)
def set_status(center_id: int, data: CenterStatusUpdate, actor: User = Depends(require_roles(*CENTER_STAFF)), db: Session = Depends(get_db)):
    return _out(RecyclingCenterService(db).set_status(actor, center_id, data.status))


@router.put("/{center_id}/manager", response_model=CenterOut)
def assign_manager(center_id: int, data: AssignManager, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return _out(RecyclingCenterService(db).assign_manager(actor, center_id, data.manager_id))


@router.put("/{center_id}/accepted-categories", response_model=CenterOut)
def set_categories(center_id: int, data: AcceptedCategories, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return _out(RecyclingCenterService(db).set_accepted_categories(actor, center_id, data.category_ids))


@router.get("/{center_id}/availability", response_model=CenterAvailability)
def availability(center_id: int, _: User = Depends(require_roles(*INTERNAL_STAFF)), db: Session = Depends(get_db)):
    return RecyclingCenterService(db).availability(center_id)


@router.delete("/{center_id}", response_model=MessageResponse)
def delete_center(center_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    RecyclingCenterService(db).delete(actor, center_id)
    return {"message": "Recycling center deleted"}
