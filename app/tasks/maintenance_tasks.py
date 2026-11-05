from sqlalchemy.orm import Session

from app.services.maintenance_service import MaintenanceService


def run(db: Session) -> int:
    """Raise 'maintenance due' notifications (call daily from cron / a scheduler)."""
    return MaintenanceService(db).raise_due_notifications()
