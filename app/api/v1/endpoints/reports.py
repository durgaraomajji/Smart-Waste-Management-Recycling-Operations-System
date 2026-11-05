from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.core.pagination import PageParams
from app.core.permissions import MANAGEMENT
from app.database.session import get_db
from app.dependencies import require_roles
from app.models import User
from app.repositories.analytics_repository import ReportFilters
from app.schemas.reports import ReportResponse
from app.services.report_service import REPORTS, ReportService
from app.utils.csv_export import rows_to_csv

router = APIRouter(prefix="/reports", tags=["Reports"])


def _filters(date_from: date | None, date_to: date | None, zone_id: int | None, waste_category_id: int | None) -> ReportFilters:
    if date_from and date_to and date_from > date_to:
        raise BadRequestError("date_from must be on or before date_to")
    return ReportFilters(date_from, date_to, zone_id, waste_category_id)


@router.get("", summary="List available reports")
def available(_: User = Depends(require_roles(*MANAGEMENT))):
    return {"reports": list(REPORTS)}


@router.get("/{report}", response_model=ReportResponse, summary="Run a report (filters, sorting, pagination)")
def run_report(
    report: str,
    params: PageParams = Depends(),
    date_from: date | None = None,
    date_to: date | None = None,
    zone_id: int | None = None,
    waste_category_id: int | None = None,
    status: str | None = None,
    sort_by: str | None = None,
    order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_roles(*MANAGEMENT)),
    db: Session = Depends(get_db),
):
    f = _filters(date_from, date_to, zone_id, waste_category_id)
    return ReportService(db).generate(report, f, status, sort_by, order, params)


@router.get("/{report}/export", summary="CSV export (all rows, no pagination)")
def export_report(
    report: str,
    date_from: date | None = None,
    date_to: date | None = None,
    zone_id: int | None = None,
    waste_category_id: int | None = None,
    status: str | None = None,
    sort_by: str | None = None,
    order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_roles(*MANAGEMENT)),
    db: Session = Depends(get_db),
):
    f = _filters(date_from, date_to, zone_id, waste_category_id)
    data = ReportService(db).generate(report, f, status, sort_by, order, None)
    return Response(
        content=rows_to_csv(data["items"]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report}.csv"'},
    )
