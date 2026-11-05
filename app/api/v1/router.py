from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    assignments,
    audit_logs,
    auth,
    collections,
    complaints,
    customers,
    dashboard,
    disposal,
    locations,
    maintenance,
    notifications,
    pickup_requests,
    processing,
    recycling_centers,
    reports,
    segregation,
    transfers,
    users,
    vehicles,
    waste_categories,
    workforce,
)

api_router = APIRouter()
for module in (
    auth, users, locations, waste_categories, customers, pickup_requests, vehicles, workforce,
    assignments, collections, recycling_centers, transfers, segregation, processing, disposal,
    maintenance, complaints, notifications, analytics, dashboard, reports, audit_logs,
):
    api_router.include_router(module.router)
