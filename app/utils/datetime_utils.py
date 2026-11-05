from datetime import date, datetime, timedelta, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (matches how the database columns are stored)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hours_between(start: datetime, end: datetime) -> float:
    return round((end - start).total_seconds() / 3600, 2)


def minutes_between(start: datetime, end: datetime) -> float:
    return round((end - start).total_seconds() / 60, 2)


def add_days(d: date, days: int) -> date:
    return d + timedelta(days=days)
