from app.enums import UserRole
from tests.factories.flow import World
from tests.factories.user_factory import create_user
from tests.factories.waste_factory import category_id

B = "/api/v1/recycling-centers"


def test_register_center_with_categories(client, db):
    w = World(client, db)
    c = w.center(categories=[category_id(db, "PLS"), category_id(db, "PPR")])
    assert len(c["accepted_category_ids"]) == 2 and c["status"] == "active"
    assert client.post(B, json={"name": "Center RC1", "code": "RCX", "address": "Somewhere", "daily_capacity_kg": 10}, headers=w.h).status_code == 409
    assert client.get(f"{B}?category_id={category_id(db, 'PPR')}", headers=w.h).json()["total"] == 1
    av = client.get(f"{B}/{c['id']}/availability", headers=w.h).json()
    assert av["available_capacity_kg"] == 5000 and av["utilization_pct"] == 0


def test_manager_must_hold_manager_role(client, db):
    w = World(client, db)
    c = w.center()
    cust = create_user(db, UserRole.CUSTOMER, "nc@example.com")
    mgr = create_user(db, UserRole.RECYCLING_CENTER_MANAGER, "mgr@example.com")
    assert client.put(f"{B}/{c['id']}/manager", json={"manager_id": cust.id}, headers=w.h).status_code == 400
    r = client.put(f"{B}/{c['id']}/manager", json={"manager_id": mgr.id}, headers=w.h)
    assert r.status_code == 200 and r.json()["manager_id"] == mgr.id


def test_unknown_category_rejected(client, db):
    w = World(client, db)
    r = client.post(B, json={"name": "Bad", "code": "BAD", "address": "Nowhere", "daily_capacity_kg": 10, "accepted_category_ids": [9999]}, headers=w.h)
    assert r.status_code == 404
