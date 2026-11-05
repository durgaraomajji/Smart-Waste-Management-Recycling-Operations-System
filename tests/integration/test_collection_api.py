from tests.factories.flow import World

B = "/api/v1/collections"


def test_full_collection_lifecycle(client, db):
    w = World(client, db)
    w.assign()
    w.start()
    assert client.get(f"/api/v1/vehicles/{w.vehicle['id']}", headers=w.h).json()["status"] == "in_service"
    done = w.complete(90).json()
    assert done["status"] == "completed" and done["collected_quantity_kg"] == 90 and done["completed_at"]
    assert client.get(f"/api/v1/pickup-requests/{w.pickup['id']}", headers=w.h).json()["status"] == "collected"
    assert client.get(f"/api/v1/vehicles/{w.vehicle['id']}", headers=w.h).json()["status"] == "available"
    assert client.get(f"{B}?status=completed", headers=w.h).json()["total"] == 1


def test_cannot_complete_twice_or_exceed_capacity(client, db):
    w = World(client, db, capacity=200.0)
    w.assign()
    w.start()
    w.complete(500, expect=422)  # above vehicle capacity
    w.complete(150)
    w.complete(150, expect=422)  # already completed


def test_missed_pickup_returns_to_queue_and_notifies(client, db):
    w = World(client, db)
    w.assign()
    w.start()
    r = client.post(f"{B}/{w.record['id']}/incomplete", json={"reason": "Gate locked", "missed": True}, headers=w.h)
    assert r.status_code == 200 and r.json()["status"] == "missed"
    assert client.get(f"/api/v1/pickup-requests/{w.pickup['id']}", headers=w.h).json()["status"] == "approved"
    notes = client.get("/api/v1/notifications", headers=w.h).json()["items"]
    assert any(n["notification_type"] == "missed_collection" for n in notes)


def test_partial_pickup_requires_quantity(client, db):
    w = World(client, db)
    w.assign()
    w.start()
    assert client.post(f"{B}/{w.record['id']}/incomplete", json={"reason": "Truck full"}, headers=w.h).status_code == 422
    ok = client.post(f"{B}/{w.record['id']}/incomplete", json={"reason": "Truck full", "collected_quantity_kg": 40}, headers=w.h)
    assert ok.json()["status"] == "incomplete"


def test_photo_urls_must_be_valid(client, db):
    w = World(client, db)
    w.assign()
    w.start()
    r = client.post(f"{B}/{w.record['id']}/complete", json={"collected_quantity_kg": 10, "photo_urls": ["not-a-url"]}, headers=w.h)
    assert r.status_code == 422
