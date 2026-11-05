from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.repositories.analytics_repository import ReportFilters
from app.services.report_service import ReportService
from app.utils.csv_export import rows_to_csv


def daily_collection_csv(db: Session, day: date | None = None) -> str:
    day = day or date.today() - timedelta(days=1)
    rows = ReportService(db).rows("daily-collection", ReportFilters(date_from=day, date_to=day))
    return rows_to_csv(rows)
