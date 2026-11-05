from datetime import datetime, timedelta

from sqlalchemy import select

from app.enums import AssignmentStatus
from app.models import AssignmentHistory, CollectionAssignment
from app.models.collection_assignment import assignment_workers
from app.repositories.base_repository import BaseRepository

ACTIVE = (AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS)
SLOT = timedelta(hours=2)  # a collection occupies a driver/vehicle/worker for this long when checking clashes


class AssignmentRepository(BaseRepository[CollectionAssignment]):
    model = CollectionAssignment

    def active_for_pickup(self, pickup_id: int) -> CollectionAssignment | None:
        return self.db.scalar(
            self.select().where(
                CollectionAssignment.pickup_request_id == pickup_id, CollectionAssignment.status.in_(ACTIVE)
            )
        )

    def _clashing(self, when: datetime, exclude_id: int | None):
        stmt = self.select().where(
            CollectionAssignment.status.in_(ACTIVE),
            CollectionAssignment.scheduled_at > when - SLOT,
            CollectionAssignment.scheduled_at < when + SLOT,
        )
        if exclude_id:
            stmt = stmt.where(CollectionAssignment.id != exclude_id)
        return stmt

    def driver_busy(self, driver_id: int, when: datetime, exclude_id: int | None = None) -> bool:
        return self.count(self._clashing(when, exclude_id).where(CollectionAssignment.driver_id == driver_id)) > 0

    def vehicle_busy(self, vehicle_id: int, when: datetime, exclude_id: int | None = None) -> bool:
        return self.count(self._clashing(when, exclude_id).where(CollectionAssignment.vehicle_id == vehicle_id)) > 0

    def worker_busy(self, worker_id: int, when: datetime, exclude_id: int | None = None) -> bool:
        stmt = (
            self._clashing(when, exclude_id)
            .join(assignment_workers, assignment_workers.c.assignment_id == CollectionAssignment.id)
            .where(assignment_workers.c.worker_id == worker_id)
        )
        return self.count(stmt) > 0

    def filtered(self, status: AssignmentStatus | None = None, driver_id: int | None = None, vehicle_id: int | None = None):
        stmt = self.select()
        if status:
            stmt = stmt.where(CollectionAssignment.status == status)
        if driver_id:
            stmt = stmt.where(CollectionAssignment.driver_id == driver_id)
        if vehicle_id:
            stmt = stmt.where(CollectionAssignment.vehicle_id == vehicle_id)
        return stmt.order_by(CollectionAssignment.scheduled_at.desc())

    def for_worker(self, worker_id: int):
        return (
            self.select()
            .join(assignment_workers, assignment_workers.c.assignment_id == CollectionAssignment.id)
            .where(assignment_workers.c.worker_id == worker_id)
            .order_by(CollectionAssignment.scheduled_at.desc())
        )

    # ---- history ----
    def add_history(self, **kwargs) -> AssignmentHistory:
        h = AssignmentHistory(**kwargs)
        self.db.add(h)
        self.db.flush()
        return h

    def history(self, assignment_id: int):
        return select(AssignmentHistory).where(AssignmentHistory.assignment_id == assignment_id).order_by(AssignmentHistory.id)
