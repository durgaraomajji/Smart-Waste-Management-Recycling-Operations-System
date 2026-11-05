from datetime import date

from app.models import WasteSegregation
from app.repositories.base_repository import BaseRepository, day_end, day_start


class SegregationRepository(BaseRepository[WasteSegregation]):
    model = WasteSegregation

    def filtered(self, center_id: int | None = None, waste_category_id: int | None = None, date_from: date | None = None, date_to: date | None = None):
        stmt = self.select()
        if center_id:
            stmt = stmt.where(WasteSegregation.center_id == center_id)
        if waste_category_id:
            stmt = stmt.where(WasteSegregation.waste_category_id == waste_category_id)
        if date_from:
            stmt = stmt.where(WasteSegregation.created_at >= day_start(date_from))
        if date_to:
            stmt = stmt.where(WasteSegregation.created_at <= day_end(date_to))
        return stmt.order_by(WasteSegregation.id.desc())
