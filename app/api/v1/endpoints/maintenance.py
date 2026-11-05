from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import INTERNAL_STAFF, MANAGEMENT, SUPERVISION
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import MaintenanceStatus, MaintenanceType, UserRole
from app.models import User
from app.schemas.maintenance import (
    BreakdownReport,
    MaintenanceComplete,
    MaintenanceRequestCreate,
    MaintenanceRequestOut,
    MaintenanceScheduleOut,
    ScheduleCreate,
    TechnicianAssign,
)
from app.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["Vehicle Maintenance"])

TECH = (*SUPERVISION, UserRole.DRIVER)


@router.post("/requests", response_model=MaintenanceRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(data: MaintenanceRequestCreate, actor: User = Depends(require_roles(*TECH)), db: Session = Depends(get_db)):
    return MaintenanceService(db).create_request(actor, data)


@router.post("/breakdowns", response_model=MaintenanceRequestOut, status_code=status.HTTP_201_CREATED, summary="Report a breakdown (marks vehicle broken down)")
def report_breakdown(data: BreakdownReport, actor: User = Depends(require_roles(*TECH)), db: Session = Depends(get_db)):
    return MaintenanceService(db).report_breakdown(actor, data)


@router.get("/requests", response_model=Page[MaintenanceRequestOut])
def list_requests(
    params: PageParams = Depends(),
    vehicle_id: int | None = None,
    status: MaintenanceStatus | None = None,
    maintenance_type: MaintenanceType | None = None,
    _: User = Depends(require_roles(*SUPERVISION)),
    db: Session = Depends(get_db),
):
    return MaintenanceService(db).list(params, vehicle_id=vehicle_id, status=status, maintenance_type=maintenance_type)


@router.get("/requests/{request_id}", response_model=MaintenanceRequestOut)
def get_request(request_id: int, _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return MaintenanceService(db).get(request_id)


@router.patch("/requests/{request_id}/technician", response_model=MaintenanceRequestOut)
def assign_technician(request_id: int, data: TechnicianAssign, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return MaintenanceService(db).assign_technician(actor, request_id, data)


@router.post("/requests/{request_id}/start", response_model=MaintenanceRequestOut)
def start(request_id: int, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return MaintenanceService(db).start(actor, request_id)


@router.post("/requests/{request_id}/complete", response_model=MaintenanceRequestOut, summary="Complete: records cost and downtime")
def complete(request_id: int, data: MaintenanceComplete, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return MaintenanceService(db).complete(actor, request_id, data)


@router.post("/requests/{request_id}/cancel", response_model=MaintenanceRequestOut)
def cancel(request_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return MaintenanceService(db).cancel(actor, request_id)


@router.post("/schedules", response_model=MaintenanceScheduleOut, status_code=status.HTTP_201_CREATED, summary="Preventive maintenance schedule")
def create_schedule(data: ScheduleCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return MaintenanceService(db).create_schedule(actor, data)


@router.get("/vehicles/{vehicle_id}/schedules", response_model=Page[MaintenanceScheduleOut])
def list_schedules(vehicle_id: int, params: PageParams = Depends(), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return MaintenanceService(db).list_schedules(vehicle_id, params)


@router.post("/due-check", summary="Raise 'maintenance due' notifications now")
def due_check(_: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return {"notifications_created": MaintenanceService(db).raise_due_notifications()}
