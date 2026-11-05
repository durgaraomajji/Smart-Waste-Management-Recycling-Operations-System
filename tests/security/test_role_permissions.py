import pytest

from app.enums import UserRole
from tests.factories.user_factory import headers_for

# (method, url, roles that must be refused)
FORBIDDEN = [
    ("post", "/api/v1/vehicles", [UserRole.CUSTOMER, UserRole.DRIVER, UserRole.FIELD_WORKER, UserRole.COLLECTION_SUPERVISOR]),
    ("get", "/api/v1/dashboard", [UserRole.CUSTOMER, UserRole.DRIVER, UserRole.COLLECTION_SUPERVISOR]),
    ("get", "/api/v1/audit-logs", [UserRole.CUSTOMER, UserRole.COLLECTION_SUPERVISOR, UserRole.DRIVER]),
    ("get", "/api/v1/users", [UserRole.CUSTOMER, UserRole.DRIVER, UserRole.RECYCLING_CENTER_MANAGER]),
    ("post", "/api/v1/users", [UserRole.OPERATIONS_MANAGER, UserRole.CUSTOMER]),
    ("get", "/api/v1/reports", [UserRole.CUSTOMER, UserRole.FIELD_WORKER]),
    ("get", "/api/v1/customers", [UserRole.CUSTOMER, UserRole.DRIVER]),
    ("post", "/api/v1/segregation", [UserRole.CUSTOMER, UserRole.DRIVER, UserRole.COLLECTION_SUPERVISOR]),
    ("post", "/api/v1/assignments", [UserRole.CUSTOMER, UserRole.DRIVER, UserRole.RECYCLING_CENTER_MANAGER]),
]


@pytest.mark.parametrize("method,url,roles", FORBIDDEN)
def test_forbidden_roles_get_403(client, db, method, url, roles):
    for role in roles:
        r = getattr(client, method)(url, headers=headers_for(client, db, role), **({"json": {}} if method == "post" else {}))
        assert r.status_code == 403, f"{role.value} -> {method.upper()} {url} returned {r.status_code}"


def test_super_admin_passes_every_role_gate(client):
    from tests.factories.user_factory import admin_headers
    h = admin_headers(client)
    for url in ("/api/v1/dashboard", "/api/v1/audit-logs", "/api/v1/users", "/api/v1/reports", "/api/v1/customers"):
        assert client.get(url, headers=h).status_code == 200


def test_ops_manager_can_use_management_endpoints(client, db):
    h = headers_for(client, db, UserRole.OPERATIONS_MANAGER)
    assert client.get("/api/v1/dashboard", headers=h).status_code == 200
    assert client.get("/api/v1/users", headers=h).status_code == 200


def test_driver_only_sees_own_assignments(client, db):
    from tests.factories.flow import World
    from tests.factories.user_factory import create_user, login
    w = World(client, db)
    w.assign()
    drv_user = create_user(db, UserRole.DRIVER, "drv@example.com")
    h = login(client, "drv@example.com")
    assert client.get("/api/v1/assignments", headers=h).json()["total"] == 0
    assert client.get(f"/api/v1/assignments/{w.assignment['id']}", headers=h).status_code == 403
    assert client.post("/api/v1/collections/start", json={"assignment_id": w.assignment["id"]}, headers=h).status_code == 403
    # linking the driver profile to that user grants access
    from app.models import Driver
    db.query(Driver).filter_by(id=w.driver["id"]).update({"user_id": drv_user.id})
    db.commit()
    assert client.get("/api/v1/assignments", headers=h).json()["total"] == 1
    assert client.post("/api/v1/collections/start", json={"assignment_id": w.assignment["id"]}, headers=h).status_code == 201


def test_center_manager_limited_to_own_center(client, db):
    from tests.factories.flow import World
    from tests.factories.user_factory import create_user, login
    w = World(client, db)
    mine, other = w.center(code="MINE"), w.center(code="OTHER")
    mgr = create_user(db, UserRole.RECYCLING_CENTER_MANAGER, "m@example.com")
    client.put(f"/api/v1/recycling-centers/{mine['id']}/manager", json={"manager_id": mgr.id}, headers=w.h)
    h = login(client, "m@example.com")
    from tests.factories.waste_factory import category_id
    from datetime import date
    body = {"waste_category_id": category_id(db, "PLS"), "input_quantity_kg": 1, "processing_date": date.today().isoformat()}
    assert client.post("/api/v1/processing/batches", json={**body, "center_id": other["id"]}, headers=h).status_code == 403
    assert client.post("/api/v1/processing/batches", json={**body, "center_id": mine["id"]}, headers=h).status_code == 422  # allowed, but centre holds no waste
