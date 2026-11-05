from app.enums import RecyclabilityStatus
from app.models import SegregationRule, WasteCategory
from app.repositories.base_repository import BaseRepository


class WasteCategoryRepository(BaseRepository[WasteCategory]):
    model = WasteCategory

    def filtered(self, search: str | None = None, recyclability: RecyclabilityStatus | None = None, is_active: bool | None = None):
        stmt = self.select()
        if search:
            stmt = stmt.where(WasteCategory.name.ilike(f"%{search}%"))
        if recyclability:
            stmt = stmt.where(WasteCategory.recyclability == recyclability)
        if is_active is not None:
            stmt = stmt.where(WasteCategory.is_active.is_(is_active))
        return stmt.order_by(WasteCategory.name)


class SegregationRuleRepository(BaseRepository[SegregationRule]):
    model = SegregationRule
