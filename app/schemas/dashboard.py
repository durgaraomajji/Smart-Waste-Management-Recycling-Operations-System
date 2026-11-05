from pydantic import BaseModel


class DashboardOut(BaseModel):
    total_customers: int
    total_collection_requests: int
    completed_collections: int
    pending_pickups: int
    missed_collections: int
    total_vehicles: int
    available_vehicles: int
    active_recycling_centers: int
    total_waste_collected_kg: float
    total_waste_recycled_kg: float
    recycling_efficiency_pct: float
    pending_complaints: int
    vehicle_maintenance_status: dict[str, int]
