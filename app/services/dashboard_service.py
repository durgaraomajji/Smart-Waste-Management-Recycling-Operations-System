from sqlalchemy.orm import Session

from app.repositories.analytics_repository import AnalyticsRepository, ReportFilters
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardOut
from app.utils.calculation_utils import recycling_percentage


class DashboardService:
    def __init__(self, db: Session):
        self.repo = DashboardRepository(db)
        self.analytics = AnalyticsRepository(db)

    def summary(self) -> DashboardOut:
        f = ReportFilters()
        collected = self.analytics.total_collected_kg(f)
        recycled = self.analytics.total_recycled_kg(f)
        return DashboardOut(
            total_customers=self.repo.total_customers(),
            total_collection_requests=self.repo.total_requests(),
            completed_collections=self.repo.completed_collections(),
            pending_pickups=self.repo.pending_pickups(),
            missed_collections=self.analytics.missed_count(f),
            total_vehicles=self.repo.total_vehicles(),
            available_vehicles=self.repo.available_vehicles(),
            active_recycling_centers=self.repo.active_centers(),
            total_waste_collected_kg=round(collected, 2),
            total_waste_recycled_kg=round(recycled, 2),
            recycling_efficiency_pct=recycling_percentage(recycled, collected),
            pending_complaints=self.repo.pending_complaints(),
            vehicle_maintenance_status=self.repo.maintenance_status(),
        )
