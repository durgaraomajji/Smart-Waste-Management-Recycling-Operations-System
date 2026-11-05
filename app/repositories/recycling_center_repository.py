from app.enums import CenterStatus
from app.models import CenterWasteCategory, RecyclingCenter
from app.repositories.base_repository import BaseRepository


class RecyclingCenterRepository(BaseRepository[RecyclingCenter]):
    model = RecyclingCenter

    def filtered(self, status: CenterStatus | None = None, zone_id: int | None = None, search: str | None = None, category_id: int | None = None):
        stmt = self.select()
        if status:
            stmt = stmt.where(RecyclingCenter.status == status)
        if zone_id:
            stmt = stmt.where(RecyclingCenter.zone_id == zone_id)
        if search:
            stmt = stmt.where(RecyclingCenter.name.ilike(f"%{search}%"))
        if category_id:
            stmt = stmt.join(CenterWasteCategory, CenterWasteCategory.center_id == RecyclingCenter.id).where(
                CenterWasteCategory.waste_category_id == category_id
            )
        return stmt.order_by(RecyclingCenter.name)

    def set_categories(self, center: RecyclingCenter, category_ids: list[int]) -> None:
        center.accepted_categories.clear()
        self.db.flush()
        for cid in sorted(set(category_ids)):
            center.accepted_categories.append(CenterWasteCategory(center_id=center.id, waste_category_id=cid))
        self.db.flush()

    def accepts(self, center: RecyclingCenter, category_id: int) -> bool:
        return any(a.waste_category_id == category_id for a in center.accepted_categories)
