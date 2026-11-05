from tests.factories.flow import World
from tests.factories.pickup_factory import slot

B = "/api/v1/assignments"


def test_assign_updates_statuses_and_history(client, db):
    w = World(client, db)
    a = w.assign().json()
    assert a["status"] == "assigned" and len(a["workers"]) == 1
    assert client.get(f"/api/v1/pickup-requests/{w.pickup['id']}", headers=w.h).json()["status"] == "assigned"
    assert client.get(f"/api/v1/vehicles/{w.vehicle['id']}", headers=w.h).json()["status"] == "assigned"
    assert client.get(f"/api/v1/workforce/drivers/{w.driver['id']}", headers=w.h).json()["status"] == "assigned"
    hist = client.get(f"{B}/{a['id']}/history", headers=w.h).json()
    assert hist["total"] == 1 and hist["items"][0]["action"] == "assigned"


def test_capacity_validation(client, db):
    w = World(client, db, qty=800.0, capacity=500.0)
    r = w.assign(expect=422)
    assert "capacity" in r.json()["error"]["message"].lower()


def test_unavailable_vehicle_blocked(client, db):
    w = World(client, db)
    client.patch(f"/api/v1/vehicles/{w.vehicle['id']}/status", json={"status": "under_maintenance"}, headers=w.h)
    r = w.assign(expect=422)
    assert "not available" in r.json()["error"]["message"]


def test_on_leave_driver_blocked(client, db):
    w = World(client, db)
    client.patch(f"/api/v1/workforce/drivers/{w.driver['id']}/status", json={"status": "on_leave"}, headers=w.h)
    w.assign(expect=422)


def test_pending_pickup_cannot_be_assigned(client, db):
    from tests.factories.pickup_factory import make_pickup
    from tests.factories.vehicle_factory import make_driver, make_vehicle
    w = World(client, db)
    other = make_pickup(client, db, w.h, zone=w.zone)  # still pending
    w.assign(expect=422, pickup_request_id=other["id"])


def test_double_booking_blocked(client, db):
    from tests.factories.pickup_factory import approved_pickup
    w = World(client, db)
    w.assign(hours=24)
    second = approved_pickup(client, db, w.h, zone=w.zone)
    r = client.post(B, json={"pickup_request_id": second["id"], "driver_id": w.driver["id"], "vehicle_id": w.vehicle["id"], "worker_ids": [], "scheduled_at": slot(25)}, headers=w.h)
    assert r.status_code == 422 and "already has a collection" in r.json()["error"]["message"]


def test_reassign_driver_frees_old_one(client, db):
    from tests.factories.vehicle_factory import make_driver
    w = World(client, db)
    a = w.assign().json()
    d2 = make_driver(client, w.h, code="DRV9", license_no="LIC-009")
    r = client.patch(f"{B}/{a['id']}/reassign", json={"driver_id": d2["id"]}, headers=w.h)
    assert r.status_code == 200 and r.json()["driver_id"] == d2["id"]
    assert client.get(f"/api/v1/workforce/drivers/{w.driver['id']}", headers=w.h).json()["status"] == "available"
    assert client.get(f"/api/v1/workforce/drivers/{d2['id']}", headers=w.h).json()["status"] == "assigned"
    assert client.get(f"{B}/{a['id']}/history", headers=w.h).json()["total"] == 2


def test_schedule_confirmation_and_cancel_releases_resources(client, db):
    w = World(client, db)
    a = w.assign().json()
    assert client.patch(f"{B}/{a['id']}/schedule", json={"scheduled_at": slot(30)}, headers=w.h).status_code == 200
    assert client.get(f"/api/v1/pickup-requests/{w.pickup['id']}", headers=w.h).json()["status"] == "scheduled"
    assert client.post(f"/api/v1/pickup-requests/{w.pickup['id']}/cancel", json={"reason": "changed mind"}, headers=w.h).status_code == 200
    assert client.get(f"/api/v1/vehicles/{w.vehicle['id']}", headers=w.h).json()["status"] == "available"
