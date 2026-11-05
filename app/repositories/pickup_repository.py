from datetime import date

from app.enums import PickupStatus, Priority
from app.models import PickupRequest
from app.repositories.base_repository import BaseRepository


class PickupRepository(BaseRepository[PickupRequest]):
    model = PickupRequest

    def filtered(
        self,
        status: PickupStatus | None = None,
        priority: Priority | None = None,
        customer_id: int | None = None,
        zone_id: int | None = None,
        waste_category_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(PickupRequest.status == status)
        if priority:
            stmt = stmt.where(PickupRequest.priority == priority)
        if customer_id:
            stmt = stmt.where(PickupRequest.customer_id == customer_id)
        if zone_id:
            stmt = stmt.where(PickupRequest.zone_id == zone_id)
        if waste_category_id:
            stmt = stmt.where(PickupRequest.waste_category_id == waste_category_id)
        if date_from:
            stmt = stmt.where(PickupRequest.preferred_date >= date_from)
        if date_to:
            stmt = stmt.where(PickupRequest.preferred_date <= date_to)
        return stmt.order_by(PickupRequest.id.desc())
