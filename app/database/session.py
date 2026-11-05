from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_engine_kwargs: dict = {"pool_pre_ping": True}
if _is_sqlite:
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}
    if ":memory:" in settings.DATABASE_URL:
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
