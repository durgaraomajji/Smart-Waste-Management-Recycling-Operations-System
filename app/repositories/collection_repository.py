from datetime import date

from app.enums import CollectionStatus
from app.models import CollectionRecord
from app.models.pickup_request import PickupRequest
from app.repositories.base_repository import BaseRepository, day_end, day_start


class CollectionRepository(BaseRepository[CollectionRecord]):
    model = CollectionRecord

    def for_assignment(self, assignment_id: int) -> CollectionRecord | None:
        return self.db.scalar(
            self.select().where(CollectionRecord.assignment_id == assignment_id).order_by(CollectionRecord.id.desc())
        )

    def filtered(
        self,
        status: CollectionStatus | None = None,
        pickup_request_id: int | None = None,
        customer_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(CollectionRecord.status == status)
        if pickup_request_id:
            stmt = stmt.where(CollectionRecord.pickup_request_id == pickup_request_id)
        if customer_id:
            stmt = stmt.join(PickupRequest, PickupRequest.id == CollectionRecord.pickup_request_id).where(
                PickupRequest.customer_id == customer_id
            )
        if date_from:
            stmt = stmt.where(CollectionRecord.created_at >= day_start(date_from))
        if date_to:
            stmt = stmt.where(CollectionRecord.created_at <= day_end(date_to))
        return stmt.order_by(CollectionRecord.id.desc())
