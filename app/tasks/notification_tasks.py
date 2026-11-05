"""Periodic job: pending-approval reminders and centre capacity alerts."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import CENTER_CAPACITY_ALERT_THRESHOLD
from app.database.transaction import transaction
from app.enums import DisposalStatus, NotificationType, PickupStatus
from app.models import DisposalRecord, PickupRequest, RecyclingCenter
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService


def run(db: Session) -> int:
    notify, repo, created = NotificationService(db), NotificationRepository(db), 0
    with transaction(db):
        for p in db.scalars(select(PickupRequest).where(PickupRequest.is_deleted.is_(False), PickupRequest.status == PickupStatus.PENDING)):
            if not repo.exists_unread(NotificationType.PENDING_APPROVAL, "pickup_request", p.id):
                notify.notify_management(NotificationType.PENDING_APPROVAL, "Pickup awaiting approval", p.request_no, "pickup_request", p.id)
                created += 1
        for d in db.scalars(select(DisposalRecord).where(DisposalRecord.is_deleted.is_(False), DisposalRecord.status == DisposalStatus.PENDING_APPROVAL)):
            if not repo.exists_unread(NotificationType.PENDING_APPROVAL, "disposal_record", d.id):
                notify.notify_management(NotificationType.PENDING_APPROVAL, "Disposal awaiting approval", d.disposal_no, "disposal_record", d.id)
                created += 1
        for c in db.scalars(select(RecyclingCenter).where(RecyclingCenter.is_deleted.is_(False))):
            if c.daily_capacity_kg and c.current_load_kg / c.daily_capacity_kg >= CENTER_CAPACITY_ALERT_THRESHOLD:
                if not repo.exists_unread(NotificationType.CENTER_CAPACITY_ALERT, "recycling_center", c.id):
                    notify.notify_management(NotificationType.CENTER_CAPACITY_ALERT, "Center capacity alert", f"{c.name} is nearly full", "recycling_center", c.id)
                    created += 1
    return created
