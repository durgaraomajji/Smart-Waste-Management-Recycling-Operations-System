from pydantic import BaseModel


class CollectionPerformance(BaseModel):
    total_pickup_requests: int
    completed_pickups: int
    missed_pickups: int
    cancelled_pickups: int
    average_collection_time_minutes: float
    collection_efficiency_pct: float


class ZonePerformance(BaseModel):
    zone_id: int
    zone_name: str
    total_requests: int
    completed: int
    missed: int
    efficiency_pct: float
    total_collected_kg: float


class DriverPerformance(BaseModel):
    driver_id: int
    driver_name: str
    assignments: int
    completed: int
    missed: int
    efficiency_pct: float
    total_collected_kg: float
    average_collection_time_minutes: float


class VehicleUtilization(BaseModel):
    vehicle_id: int
    registration_number: str
    capacity_kg: float
    trips: int
    total_collected_kg: float
    utilization_pct: float


class CategoryDistribution(BaseModel):
    category_id: int
    category_name: str
    collected_kg: float
    percentage: float


class MonthlyTrend(BaseModel):
    month: str
    input_kg: float
    recycled_kg: float
    recycling_pct: float


class EnvironmentalImpact(BaseModel):
    total_waste_collected_kg: float
    total_recyclable_kg: float
    total_recycled_kg: float
    total_disposed_kg: float
    recycling_percentage: float
    category_distribution: list[CategoryDistribution]
    monthly_trends: list[MonthlyTrend]
    formulas: dict[str, str]
