from datetime import date, datetime, time
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base_model import utcnow

M = TypeVar("M")


def day_start(d: date) -> datetime:
    return datetime.combine(d, time.min)


def day_end(d: date) -> datetime:
    return datetime.combine(d, time.max)


class BaseRepository(Generic[M]):
    """Generic data-access helper with soft-delete awareness."""

    model: type[M]

    def __init__(self, db: Session):
        self.db = db

    # ---- reads -------------------------------------------------------------
    def _alive(self, stmt):
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        return stmt

    def select(self):
        return self._alive(select(self.model))

    def get(self, id_: int) -> M | None:
        return self.db.scalar(self.select().where(self.model.id == id_))

    def get_by(self, **kwargs) -> M | None:
        stmt = self.select()
        for k, v in kwargs.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        return self.db.scalar(stmt)

    def exists(self, **kwargs) -> bool:
        return self.get_by(**kwargs) is not None

    def all(self) -> list[M]:
        return list(self.db.scalars(self.select()).all())

    def count(self, stmt=None) -> int:
        stmt = stmt if stmt is not None else self.select()
        return self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0

    # ---- writes (no commit - services own the transaction) -------------------
    def add(self, obj: M) -> M:
        self.db.add(obj)
        self.db.flush()
        return obj

    def update(self, obj: M, data: dict) -> M:
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.flush()
        return obj

    def soft_delete(self, obj: M) -> None:
        obj.is_deleted = True
        obj.deleted_at = utcnow()
        self.db.flush()

    def next_number(self, prefix: str) -> str:
        """Human-friendly business number, e.g. PR-20261103-000042 (unique constraint is the safety net)."""
        total = self.db.scalar(select(func.count()).select_from(self.model)) or 0
        return f"{prefix}-{date.today():%Y%m%d}-{total + 1:06d}"
