from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import INTERNAL_STAFF, SUPERVISION
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import AssignmentStatus
from app.models import User
from app.schemas.collection_assignment import (
    AssignmentCreate,
    AssignmentHistoryOut,
    AssignmentOut,
    AssignmentReassign,
    ScheduleSet,
)
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Collection Assignments"])


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED, summary="Assign driver, vehicle and workers to a pickup")
def assign(data: AssignmentCreate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AssignmentService(db).assign(actor, data)


@router.get("", response_model=Page[AssignmentOut], summary="List assignments (drivers / workers see only their own)")
def list_assignments(
    params: PageParams = Depends(),
    status: AssignmentStatus | None = None,
    driver_id: int | None = None,
    vehicle_id: int | None = None,
    user: User = Depends(require_roles(*INTERNAL_STAFF)),
    db: Session = Depends(get_db),
):
    return AssignmentService(db).list(user, params, status=status, driver_id=driver_id, vehicle_id=vehicle_id)


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: int, user: User = Depends(require_roles(*INTERNAL_STAFF)), db: Session = Depends(get_db)):
    return AssignmentService(db).get(assignment_id, user)


@router.patch("/{assignment_id}/reassign", response_model=AssignmentOut, summary="Reassign a pending collection")
def reassign(assignment_id: int, data: AssignmentReassign, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AssignmentService(db).reassign(actor, assignment_id, data)


@router.patch("/{assignment_id}/schedule", response_model=AssignmentOut, summary="Confirm the collection schedule")
def set_schedule(assignment_id: int, data: ScheduleSet, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AssignmentService(db).set_schedule(actor, assignment_id, data.scheduled_at)


@router.get("/{assignment_id}/history", response_model=Page[AssignmentHistoryOut])
def assignment_history(assignment_id: int, params: PageParams = Depends(), user: User = Depends(require_roles(*INTERNAL_STAFF)), db: Session = Depends(get_db)):
    return AssignmentService(db).history(assignment_id, params, user)
