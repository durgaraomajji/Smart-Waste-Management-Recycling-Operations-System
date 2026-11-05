from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import INTERNAL_STAFF, MANAGEMENT, SUPERVISION
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import require_roles
from app.enums import WorkforceStatus
from app.models import User
from app.schemas.collection_assignment import AssignmentOut  # noqa: F401
from app.schemas.workforce import (
    DriverCreate,
    DriverOut,
    WorkerCreate,
    WorkerOut,
    WorkforceHistoryItem,
    WorkforceStatusUpdate,
    WorkforceUpdate,
)
from app.schemas.location import AssignSupervisor
from app.services.workforce_service import WorkforceService

router = APIRouter(prefix="/workforce", tags=["Drivers & Workers"])


# ------------------------------------------------------------------ drivers
@router.post("/drivers", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(data: DriverCreate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).create_driver(actor, data)


@router.get("/drivers", response_model=Page[DriverOut])
def list_drivers(
    params: PageParams = Depends(),
    status: WorkforceStatus | None = None,
    supervisor_id: int | None = None,
    search: str | None = None,
    _: User = Depends(require_roles(*SUPERVISION)),
    db: Session = Depends(get_db),
):
    return WorkforceService(db).list("driver", params, status=status, supervisor_id=supervisor_id, search=search)


@router.get("/drivers/{driver_id}", response_model=DriverOut)
def get_driver(driver_id: int, _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).get("driver", driver_id)


@router.patch("/drivers/{driver_id}", response_model=DriverOut)
def update_driver(driver_id: int, data: WorkforceUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).update(actor, "driver", driver_id, data)


@router.put("/drivers/{driver_id}/supervisor", response_model=DriverOut)
def assign_driver_supervisor(driver_id: int, data: AssignSupervisor, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return WorkforceService(db).assign_supervisor(actor, "driver", driver_id, data.supervisor_id)


@router.patch("/drivers/{driver_id}/status", response_model=DriverOut, summary="Set availability")
def set_driver_status(driver_id: int, data: WorkforceStatusUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).set_status(actor, "driver", driver_id, data.status)


@router.get("/drivers/{driver_id}/history", response_model=Page[WorkforceHistoryItem])
def driver_history(driver_id: int, params: PageParams = Depends(), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).history("driver", driver_id, params)


@router.delete("/drivers/{driver_id}", response_model=MessageResponse)
def delete_driver(driver_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    WorkforceService(db).delete(actor, "driver", driver_id)
    return {"message": "Driver deleted"}


# ------------------------------------------------------------------ workers
@router.post("/workers", response_model=WorkerOut, status_code=status.HTTP_201_CREATED)
def create_worker(data: WorkerCreate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).create_worker(actor, data)


@router.get("/workers", response_model=Page[WorkerOut])
def list_workers(
    params: PageParams = Depends(),
    status: WorkforceStatus | None = None,
    supervisor_id: int | None = None,
    search: str | None = None,
    _: User = Depends(require_roles(*SUPERVISION)),
    db: Session = Depends(get_db),
):
    return WorkforceService(db).list("worker", params, status=status, supervisor_id=supervisor_id, search=search)


@router.get("/workers/{worker_id}", response_model=WorkerOut)
def get_worker(worker_id: int, _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).get("worker", worker_id)


@router.patch("/workers/{worker_id}", response_model=WorkerOut)
def update_worker(worker_id: int, data: WorkforceUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).update(actor, "worker", worker_id, data)


@router.put("/workers/{worker_id}/supervisor", response_model=WorkerOut)
def assign_worker_supervisor(worker_id: int, data: AssignSupervisor, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return WorkforceService(db).assign_supervisor(actor, "worker", worker_id, data.supervisor_id)


@router.patch("/workers/{worker_id}/status", response_model=WorkerOut)
def set_worker_status(worker_id: int, data: WorkforceStatusUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).set_status(actor, "worker", worker_id, data.status)


@router.get("/workers/{worker_id}/history", response_model=Page[WorkforceHistoryItem])
def worker_history(worker_id: int, params: PageParams = Depends(), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return WorkforceService(db).history("worker", worker_id, params)


@router.delete("/workers/{worker_id}", response_model=MessageResponse)
def delete_worker(worker_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    WorkforceService(db).delete(actor, "worker", worker_id)
    return {"message": "Field worker deleted"}
