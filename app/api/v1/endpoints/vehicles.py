from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import INTERNAL_STAFF, MANAGEMENT, SUPERVISION
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import VehicleStatus, VehicleType
from app.models import User
from app.schemas.vehicle import (
    AvailabilityOut,
    VehicleCreate,
    VehicleMaintenanceOut,
    VehicleOut,
    VehicleStatusUpdate,
    VehicleUpdate,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(data: VehicleCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return VehicleService(db).create(actor, data)


@router.get("", response_model=Page[VehicleOut])
def list_vehicles(
    params: PageParams = Depends(),
    status: VehicleStatus | None = None,
    vehicle_type: VehicleType | None = None,
    zone_id: int | None = None,
    search: str | None = None,
    min_capacity: float | None = None,
    _: User = Depends(require_roles(*INTERNAL_STAFF)),
    db: Session = Depends(get_db),
):
    return VehicleService(db).list(
        params, status=status, vehicle_type=vehicle_type, zone_id=zone_id, search=search, min_capacity=min_capacity
    )


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, _: User = Depends(require_roles(*INTERNAL_STAFF)), db: Session = Depends(get_db)):
    return VehicleService(db).get(vehicle_id)


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, data: VehicleUpdate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return VehicleService(db).update(actor, vehicle_id, data)


@router.patch("/{vehicle_id}/status", response_model=VehicleOut)
def set_status(vehicle_id: int, data: VehicleStatusUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return VehicleService(db).set_status(actor, vehicle_id, data.status)


@router.get("/{vehicle_id}/availability", response_model=AvailabilityOut)
def availability(vehicle_id: int, _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return VehicleService(db).availability(vehicle_id)


@router.get("/{vehicle_id}/maintenance-records", response_model=Page[VehicleMaintenanceOut], summary="Maintenance records")
def maintenance_records(vehicle_id: int, params: PageParams = Depends(), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return VehicleService(db).maintenance_history(vehicle_id, params)


@router.delete("/{vehicle_id}", response_model=MessageResponse)
def delete_vehicle(vehicle_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    VehicleService(db).delete(actor, vehicle_id)
    return {"message": "Vehicle deleted"}
