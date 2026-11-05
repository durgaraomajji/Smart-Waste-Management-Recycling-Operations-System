from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.core.permissions import MANAGEMENT, SUPERVISION
from app.database.session import get_db
from app.dependencies import require_roles
from app.models import User
from app.repositories.analytics_repository import ReportFilters
from app.schemas.analytics import (
    CollectionPerformance,
    DriverPerformance,
    EnvironmentalImpact,
    VehicleUtilization,
    ZonePerformance,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def filters(date_from: date | None = None, date_to: date | None = None, zone_id: int | None = None, waste_category_id: int | None = None) -> ReportFilters:
    if date_from and date_to and date_from > date_to:
        raise BadRequestError("date_from must be on or before date_to")
    return ReportFilters(date_from, date_to, zone_id, waste_category_id)


@router.get("/collection-performance", response_model=CollectionPerformance)
def collection_performance(f: ReportFilters = Depends(filters), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AnalyticsService(db).collection_performance(f)


@router.get("/zones", response_model=list[ZonePerformance])
def zones(f: ReportFilters = Depends(filters), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AnalyticsService(db).zone_performance(f)


@router.get("/drivers", response_model=list[DriverPerformance])
def drivers(f: ReportFilters = Depends(filters), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AnalyticsService(db).driver_performance(f)


@router.get("/vehicles", response_model=list[VehicleUtilization])
def vehicles(f: ReportFilters = Depends(filters), _: User = Depends(require_roles(*SUPERVISION)), db: Session = Depends(get_db)):
    return AnalyticsService(db).vehicle_utilization(f)


@router.get("/environmental-impact", response_model=EnvironmentalImpact, summary="Totals, recycling %, distribution, trends + formulas")
def environmental(f: ReportFilters = Depends(filters), _: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return AnalyticsService(db).environmental_impact(f)
