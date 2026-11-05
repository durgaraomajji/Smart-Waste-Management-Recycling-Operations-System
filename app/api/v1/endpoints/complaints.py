from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import SUPERVISION
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import ComplaintCategory, ComplaintStatus, Priority
from app.models import User
from app.schemas.complaint import ComplaintAssign, ComplaintCreate, ComplaintHistoryOut, ComplaintOut, ComplaintStatusUpdate
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Customer Complaints"])


@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
def create_complaint(data: ComplaintCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ComplaintService(db).create(user, data)


@router.get("", response_model=Page[ComplaintOut])
def list_complaints(
    params: PageParams = Depends(),
    status: ComplaintStatus | None = None,
    category: ComplaintCategory | None = None,
    priority: Priority | None = None,
    customer_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ComplaintService(db).list(user, params, status=status, category=category, priority=priority, customer_id=customer_id)


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ComplaintService(db).get(complaint_id, user)


@router.patch("/{complaint_id}/assign", response_model=ComplaintOut, summary="Assign responsible team")
def assign(complaint_id: int, data: ComplaintAssign, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return ComplaintService(db).assign(actor, complaint_id, data)


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(complaint_id: int, data: ComplaintStatusUpdate, actor: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return ComplaintService(db).update_status(actor, complaint_id, data.status, data.remarks)


@router.get("/{complaint_id}/history", response_model=Page[ComplaintHistoryOut])
def history(complaint_id: int, params: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ComplaintService(db).history(user, complaint_id, params)
