from datetime import date

from app.enums import DisposalMethod, DisposalStatus
from app.models import DisposalRecord
from app.repositories.base_repository import BaseRepository


class DisposalRepository(BaseRepository[DisposalRecord]):
    model = DisposalRecord

    def filtered(
        self,
        status: DisposalStatus | None = None,
        method: DisposalMethod | None = None,
        waste_category_id: int | None = None,
        center_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(DisposalRecord.status == status)
        if method:
            stmt = stmt.where(DisposalRecord.method == method)
        if waste_category_id:
            stmt = stmt.where(DisposalRecord.waste_category_id == waste_category_id)
        if center_id:
            stmt = stmt.where(DisposalRecord.center_id == center_id)
        if date_from:
            stmt = stmt.where(DisposalRecord.disposal_date >= date_from)
        if date_to:
            stmt = stmt.where(DisposalRecord.disposal_date <= date_to)
        return stmt.order_by(DisposalRecord.id.desc())
