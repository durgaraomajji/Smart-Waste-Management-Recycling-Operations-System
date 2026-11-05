from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session):
    """Commit on success, roll back on any error.

    Services call `with transaction(db):` around multi-step writes so that either
    everything (incl. audit log + notifications) is persisted or nothing is.
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
