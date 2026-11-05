from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import MANAGEMENT, SUPERVISION
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import ZoneStatus
from app.models import User
from app.schemas.location import (
    AreaCreate,
    AreaOut,
    AssignSupervisor,
    ScheduleCreate,
    ScheduleOut,
    StreetCreate,
    StreetOut,
    ZoneCreate,
    ZoneDetail,
    ZoneOut,
    ZoneStatusUpdate,
    ZoneUpdate,
)
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Locations"])


# ---- zones ----------------------------------------------------------------------------------
@router.post("/zones", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(data: ZoneCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return LocationService(db).create_zone(actor, data)


@router.get("/zones", response_model=Page[ZoneOut], summary="Zone-wise search and filtering")
def list_zones(
    params: PageParams = Depends(),
    search: str | None = None,
    status: ZoneStatus | None = None,
    supervisor_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LocationService(db).list_zones(params, search=search, status=status, supervisor_id=supervisor_id)


@router.get("/zones/{zone_id}", response_model=ZoneDetail)
def get_zone(zone_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return LocationService(db).get_zone(zone_id)


@router.patch("/zones/{zone_id}", response_model=ZoneOut)
def update_zone(zone_id: int, data: ZoneUpdate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return LocationService(db).update_zone(actor, zone_id, data)


@router.patch("/zones/{zone_id}/status", response_model=ZoneOut, summary="Track zone status")
def set_zone_status(zone_id: int, data: ZoneStatusUpdate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return LocationService(db).set_zone_status(actor, zone_id, data.status)


@router.put("/zones/{zone_id}/supervisor", response_model=ZoneOut, summary="Assign a supervisor to a zone")
def assign_supervisor(zone_id: int, data: AssignSupervisor, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return LocationService(db).assign_supervisor(actor, zone_id, data.supervisor_id)


@router.delete("/zones/{zone_id}", response_model=MessageResponse)
def delete_zone(zone_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    LocationService(db).delete_zone(actor, zone_id)
    return {"message": "Zone deleted"}


# ---- areas & streets -------------------------------------------------------------------------
@router.post("/areas", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
def create_area(data: AreaCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return LocationService(db).create_area(actor, data)


@router.get("/areas", response_model=Page[AreaOut])
def list_areas(
    params: PageParams = Depends(),
    zone_id: int | None = None,
    search: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LocationService(db).list_areas(params, zone_id=zone_id, search=search)


@router.post("/areas/{area_id}/streets", response_model=StreetOut, status_code=status.HTTP_201_CREATED)
def add_street(area_id: int, data: StreetCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return LocationService(db).add_street(actor, area_id, data)


@router.get("/streets", response_model=Page[StreetOut])
def list_streets(
    params: PageParams = Depends(),
    area_id: int | None = None,
    locality: str | None = None,
    search: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LocationService(db).list_streets(params, area_id=area_id, locality=locality, search=search)


# ---- schedules -------------------------------------------------------------------------------
@router.post("/schedules", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(data: ScheduleCreate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return LocationService(db).create_schedule(actor, data)


@router.get("/schedules", response_model=Page[ScheduleOut])
def list_schedules(
    params: PageParams = Depends(),
    zone_id: int | None = None,
    day_of_week: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LocationService(db).list_schedules(params, zone_id=zone_id, day_of_week=day_of_week)


@router.patch("/schedules/{schedule_id}/deactivate", response_model=ScheduleOut)
def deactivate_schedule(schedule_id: int, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return LocationService(db).deactivate_schedule(actor, schedule_id)
