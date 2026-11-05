from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums import CenterStatus, ComplaintStatus, PickupStatus, VehicleStatus
from app.models import (
    Complaint,
    Customer,
    MaintenanceRequest,
    PickupRequest,
    RecyclingCenter,
    Vehicle,
)


def _count(db: Session, model, *conds) -> int:
    stmt = select(func.count()).select_from(model)
    if hasattr(model, "is_deleted"):
        stmt = stmt.where(model.is_deleted.is_(False))
    for c in conds:
        stmt = stmt.where(c)
    return db.scalar(stmt) or 0


class DashboardRepository:
    PENDING = (PickupStatus.PENDING, PickupStatus.APPROVED, PickupStatus.ASSIGNED, PickupStatus.SCHEDULED)
    OPEN_COMPLAINTS = (ComplaintStatus.OPEN, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS)

    def __init__(self, db: Session):
        self.db = db

    def total_customers(self) -> int:
        return _count(self.db, Customer)

    def total_requests(self) -> int:
        return _count(self.db, PickupRequest)

    def completed_collections(self) -> int:
        return _count(self.db, PickupRequest, PickupRequest.status == PickupStatus.COLLECTED)

    def pending_pickups(self) -> int:
        return _count(self.db, PickupRequest, PickupRequest.status.in_(self.PENDING))

    def total_vehicles(self) -> int:
        return _count(self.db, Vehicle, Vehicle.status != VehicleStatus.RETIRED)

    def available_vehicles(self) -> int:
        return _count(self.db, Vehicle, Vehicle.status == VehicleStatus.AVAILABLE)

    def active_centers(self) -> int:
        return _count(self.db, RecyclingCenter, RecyclingCenter.status == CenterStatus.ACTIVE)

    def pending_complaints(self) -> int:
        return _count(self.db, Complaint, Complaint.status.in_(self.OPEN_COMPLAINTS))

    def maintenance_status(self) -> dict[str, int]:
        stmt = (
            select(MaintenanceRequest.status, func.count())
            .where(MaintenanceRequest.is_deleted.is_(False))
            .group_by(MaintenanceRequest.status)
        )
        return {s.value: c for s, c in self.db.execute(stmt).all()}
