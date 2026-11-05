from sqlalchemy import select

from app.enums import ComplaintCategory, ComplaintStatus, Priority
from app.models import Complaint, ComplaintHistory
from app.repositories.base_repository import BaseRepository


class ComplaintRepository(BaseRepository[Complaint]):
    model = Complaint

    def filtered(
        self,
        status: ComplaintStatus | None = None,
        category: ComplaintCategory | None = None,
        priority: Priority | None = None,
        customer_id: int | None = None,
    ):
        stmt = self.select()
        if status:
            stmt = stmt.where(Complaint.status == status)
        if category:
            stmt = stmt.where(Complaint.category == category)
        if priority:
            stmt = stmt.where(Complaint.priority == priority)
        if customer_id:
            stmt = stmt.where(Complaint.customer_id == customer_id)
        return stmt.order_by(Complaint.id.desc())

    def add_history(self, **kwargs) -> ComplaintHistory:
        h = ComplaintHistory(**kwargs)
        self.db.add(h)
        self.db.flush()
        return h

    def history(self, complaint_id: int):
        return select(ComplaintHistory).where(ComplaintHistory.complaint_id == complaint_id).order_by(ComplaintHistory.id)
