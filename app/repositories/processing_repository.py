from datetime import date

from app.enums import ProcessingStatus
from app.models import ProcessingBatch
from app.repositories.base_repository import BaseRepository


class ProcessingRepository(BaseRepository[ProcessingBatch]):
    model = ProcessingBatch

    def filtered(
        self,
        status: ProcessingStatus | None = None,
        center_id: int | None = None,
        waste_category_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(ProcessingBatch.status == status)
        if center_id:
            stmt = stmt.where(ProcessingBatch.center_id == center_id)
        if waste_category_id:
            stmt = stmt.where(ProcessingBatch.waste_category_id == waste_category_id)
        if date_from:
            stmt = stmt.where(ProcessingBatch.processing_date >= date_from)
        if date_to:
            stmt = stmt.where(ProcessingBatch.processing_date <= date_to)
        return stmt.order_by(ProcessingBatch.id.desc())
