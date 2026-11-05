from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import get_current_user
from app.enums import NotificationStatus
from app.models import User
from app.schemas.notification import NotificationOut
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=Page[NotificationOut])
def list_notifications(
    params: PageParams = Depends(),
    status: NotificationStatus | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService(db).list_for(user, params, status)


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"unread": NotificationService(db).unread_count(user)}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return NotificationService(db).mark_read(user, notification_id)


@router.post("/read-all", response_model=MessageResponse)
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    NotificationService(db).mark_all_read(user)
    return {"message": "All notifications marked as read"}
