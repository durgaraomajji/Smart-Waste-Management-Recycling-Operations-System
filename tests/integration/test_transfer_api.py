from tests.factories.flow import World
from tests.factories.waste_factory import category_id

B = "/api/v1/transfers"


def body(w, center, kg, **over):
    d = {"source_zone_id": w.zone["id"], "center_id": center["id"], "waste_category_id": category_id(w.db, "PLS"),
         "quantity_kg": kg, "vehicle_id": w.vehicle["id"]}
    d.update(over)
    return d


def test_transfer_lifecycle_updates_center_load(client, db):
    w = World(client, db).collected(90)
    c = w.center()
    t = client.post(B, json=body(w, c, 60), headers=w.h)
    assert t.status_code == 201 and t.json()["status"] == "pending"
    tid = t.json()["id"]
    assert client.patch(f"{B}/{tid}/status", json={"status": "delivered"}, headers=w.h).status_code == 422  # must go via in_transit
    assert client.patch(f"{B}/{tid}/status", json={"status": "in_transit"}, headers=w.h).json()["dispatched_at"]
    d = client.patch(f"{B}/{tid}/status", json={"status": "delivered"}, headers=w.h)
    assert d.status_code == 200 and d.json()["delivered_at"]
    assert client.get(f"/api/v1/recycling-centers/{c['id']}", headers=w.h).json()["current_load_kg"] == 60


def test_cannot_transfer_more_than_collected_stock(client, db):
    w = World(client, db).collected(90)
    c = w.center()
    r = client.post(B, json=body(w, c, 95), headers=w.h)
    assert r.status_code == 422 and "available" in r.json()["error"]["message"]
    assert client.post(B, json=body(w, c, 60), headers=w.h).status_code == 201
    assert client.post(B, json=body(w, c, 40), headers=w.h).status_code == 422  # only 30 left


def test_center_must_accept_category_and_have_capacity(client, db):
    w = World(client, db).collected(90)
    glass_only = w.center(code="RC2", categories=[category_id(db, "GLS")])
    assert "does not accept" in client.post(B, json=body(w, glass_only, 10), headers=w.h).json()["error"]["message"]
    small = w.center(capacity=20, code="RC3")
    assert "capacity" in client.post(B, json=body(w, small, 50), headers=w.h).json()["error"]["message"].lower()


def test_inactive_center_and_vehicle_capacity(client, db):
    w = World(client, db, qty=40, capacity=50).collected(40)
    c = w.center()
    assert "exceeds vehicle capacity" in client.post(B, json=body(w, c, 55), headers=w.h).json()["error"]["message"]
    client.patch(f"/api/v1/recycling-centers/{c['id']}/status", json={"status": "maintenance"}, headers=w.h)
    assert client.post(B, json=body(w, c, 10), headers=w.h).status_code == 422


def test_capacity_alert_on_delivery(client, db):
    w = World(client, db).collected(90)
    c = w.center(capacity=100)
    t = client.post(B, json=body(w, c, 90), headers=w.h).json()
    client.patch(f"{B}/{t['id']}/status", json={"status": "in_transit"}, headers=w.h)
    client.patch(f"{B}/{t['id']}/status", json={"status": "delivered"}, headers=w.h)
    notes = client.get("/api/v1/notifications", headers=w.h).json()["items"]
    assert any(n["notification_type"] == "center_capacity_alert" for n in notes)
