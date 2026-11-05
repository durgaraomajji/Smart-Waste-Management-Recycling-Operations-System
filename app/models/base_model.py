from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class IDMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BaseModel(IDMixin, TimestampMixin, SoftDeleteMixin):
    """Common columns: id, created_at, updated_at, soft-delete flags."""
    __abstract__ = True


from sqlalchemy import Enum as SAEnum  # noqa: E402


def EnumType(enum_cls):
    """Portable enum column (VARCHAR + value mapping) that works on SQLite, MySQL and PostgreSQL."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=40,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )
