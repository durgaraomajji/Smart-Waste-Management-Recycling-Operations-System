"""Roles are a code-level enum (app.enums.UserRole), so there are no role rows to insert.

This module documents and prints the role -> capability matrix used by `require_roles`.
"""
from app.enums import UserRole

ROLE_DESCRIPTIONS = {
    UserRole.SUPER_ADMIN: "Full access, user management, audit logs",
    UserRole.OPERATIONS_MANAGER: "Zones, vehicles, approvals, reports, dashboard",
    UserRole.COLLECTION_SUPERVISOR: "Pickup approval, assignments, workforce, complaints",
    UserRole.DRIVER: "Own assignments, collection tracking, breakdown reports",
    UserRole.RECYCLING_CENTER_MANAGER: "Own center: transfers, segregation, processing, disposal",
    UserRole.FIELD_WORKER: "Own assignments, collection tracking",
    UserRole.CUSTOMER: "Own profile, pickup requests, complaints",
}


def seed_roles() -> None:
    for role, desc in ROLE_DESCRIPTIONS.items():
        print(f"{role.value:28s} {desc}")
