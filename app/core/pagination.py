from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

T = TypeVar("T")


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


def paginate(db: Session, stmt, params: PageParams) -> dict:
    """Execute a SELECT statement with pagination. Returns a dict ready for Page[...] validation."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.offset(params.offset).limit(params.page_size)).all()
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": ceil(total / params.page_size) if total else 0,
    }
