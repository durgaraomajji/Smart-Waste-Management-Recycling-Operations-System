from sqlalchemy.orm import Session

from app.enums import PickupStatus
from app.repositories.analytics_repository import AnalyticsRepository, ReportFilters
from app.schemas.analytics import (
    CategoryDistribution,
    CollectionPerformance,
    DriverPerformance,
    EnvironmentalImpact,
    MonthlyTrend,
    VehicleUtilization,
    ZonePerformance,
)
from app.utils.calculation_utils import average, collection_efficiency, percentage, recycling_percentage

FORMULAS = {
    "total_waste_collected_kg": "Sum of collected_quantity_kg over collection records with status completed or incomplete",
    "total_recyclable_kg": "Sum of recyclable_kg over waste segregation records",
    "total_waste_recycled_kg": "Sum of recycled_output_kg over processing batches with status completed",
    "total_waste_disposed_kg": "Sum of quantity_kg over disposal records with status approved or disposed",
    "recycling_percentage": "total_waste_recycled_kg / total_waste_collected_kg x 100",
    "category_distribution": "collected kg of a category / total collected kg x 100",
    "monthly_recycling_pct": "recycled_kg / input_kg x 100 for batches completed in that month",
    "assumptions": (
        "Soft-deleted rows are excluded. Zone filter applies to collection figures only (segregation, processing and "
        "disposal are centre-level). Quantities are kilograms. Processing input is deducted from centre stock when a batch is created."
    ),
}


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsRepository(db)

    def collection_performance(self, f: ReportFilters) -> CollectionPerformance:
        counts = self.repo.pickup_status_counts(f)
        total = sum(counts.values())
        completed = counts.get(PickupStatus.COLLECTED, 0)
        cancelled = counts.get(PickupStatus.CANCELLED, 0)
        excluded = cancelled + counts.get(PickupStatus.REJECTED, 0)
        return CollectionPerformance(
            total_pickup_requests=total,
            completed_pickups=completed,
            missed_pickups=self.repo.missed_count(f),
            cancelled_pickups=cancelled,
            average_collection_time_minutes=average(self.repo.collection_minutes(f)),
            collection_efficiency_pct=collection_efficiency(completed, total, excluded),
        )

    def zone_performance(self, f: ReportFilters) -> list[ZonePerformance]:
        return [ZonePerformance(**r) for r in self.repo.zone_stats(f)]

    def driver_performance(self, f: ReportFilters) -> list[DriverPerformance]:
        return [DriverPerformance(**r) for r in self.repo.driver_stats(f)]

    def vehicle_utilization(self, f: ReportFilters) -> list[VehicleUtilization]:
        return [VehicleUtilization(**r) for r in self.repo.vehicle_stats(f)]

    def environmental_impact(self, f: ReportFilters) -> EnvironmentalImpact:
        collected = self.repo.total_collected_kg(f)
        recycled = self.repo.total_recycled_kg(f)
        dist = self.repo.category_distribution(f)
        total_dist = sum(kg for _, _, kg in dist)
        return EnvironmentalImpact(
            total_waste_collected_kg=round(collected, 2),
            total_recyclable_kg=round(self.repo.total_recyclable_kg(f), 2),
            total_recycled_kg=round(recycled, 2),
            total_disposed_kg=round(self.repo.total_disposed_kg(f), 2),
            recycling_percentage=recycling_percentage(recycled, collected),
            category_distribution=[
                CategoryDistribution(category_id=cid, category_name=name, collected_kg=round(kg, 2), percentage=percentage(kg, total_dist))
                for cid, name, kg in dist
            ],
            monthly_trends=[MonthlyTrend(**m) for m in self.repo.monthly_recycling(f)],
            formulas=FORMULAS,
        )
