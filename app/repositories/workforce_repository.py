from sqlalchemy import or_

from app.enums import WorkforceStatus
from app.models import Driver, FieldWorker
from app.repositories.base_repository import BaseRepository


class _WorkforceMixin:
    def filtered(self, status: WorkforceStatus | None = None, supervisor_id: int | None = None, search: str | None = None):
        m = self.model
        stmt = self.select()
        if status:
            stmt = stmt.where(m.status == status)
        if supervisor_id:
            stmt = stmt.where(m.supervisor_id == supervisor_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(m.full_name.ilike(like), m.employee_code.ilike(like), m.phone.ilike(like)))
        return stmt.order_by(m.full_name)


class DriverRepository(_WorkforceMixin, BaseRepository[Driver]):
    model = Driver


class WorkerRepository(_WorkforceMixin, BaseRepository[FieldWorker]):
    model = FieldWorker
