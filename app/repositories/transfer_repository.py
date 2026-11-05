from datetime import date

from app.enums import TransferStatus
from app.models import WasteTransfer
from app.repositories.base_repository import BaseRepository, day_end, day_start


class TransferRepository(BaseRepository[WasteTransfer]):
    model = WasteTransfer

    def filtered(
        self,
        status: TransferStatus | None = None,
        center_id: int | None = None,
        source_zone_id: int | None = None,
        waste_category_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(WasteTransfer.status == status)
        if center_id:
            stmt = stmt.where(WasteTransfer.center_id == center_id)
        if source_zone_id:
            stmt = stmt.where(WasteTransfer.source_zone_id == source_zone_id)
        if waste_category_id:
            stmt = stmt.where(WasteTransfer.waste_category_id == waste_category_id)
        if date_from:
            stmt = stmt.where(WasteTransfer.created_at >= day_start(date_from))
        if date_to:
            stmt = stmt.where(WasteTransfer.created_at <= day_end(date_to))
        return stmt.order_by(WasteTransfer.id.desc())
