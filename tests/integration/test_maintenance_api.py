from datetime import date, timedelta

from tests.factories.user_factory import admin_headers
from tests.factories.vehicle_factory import make_vehicle

B = "/api/v1/maintenance"


def test_breakdown_marks_vehicle_and_notifies(client):
    h = admin_headers(client)
    v = make_vehicle(client, h)
    r = client.post(f"{B}/breakdowns", json={"vehicle_id": v["id"], "description": "Engine overheating"}, headers=h)
    assert r.status_code == 201 and r.json()["priority"] == "urgent"
    assert client.get(f"/api/v1/vehicles/{v['id']}", headers=h).json()["status"] == "broken_down"
    notes = client.get("/api/v1/notifications", headers=h).json()["items"]
    assert any(n["notification_type"] == "vehicle_breakdown" for n in notes)


def test_maintenance_lifecycle_records_cost_and_downtime(client):
    h = admin_headers(client)
    v = make_vehicle(client, h)
    req = client.post(f"{B}/requests", json={"vehicle_id": v["id"], "description": "Replace brake pads"}, headers=h).json()
    assert client.post(f"{B}/requests/{req['id']}/complete", json={"cost": 10}, headers=h).status_code == 422  # not started
    assert client.post(f"{B}/requests/{req['id']}/start", headers=h).status_code == 200
    assert client.get(f"/api/v1/vehicles/{v['id']}", headers=h).json()["status"] == "under_maintenance"
    done = client.post(f"{B}/requests/{req['id']}/complete", json={"cost": 450.5, "performed_by": "Garage A", "odometer_km": 12000}, headers=h).json()
    assert done["status"] == "completed" and done["cost"] == 450.5 and done["downtime_hours"] >= 0
    assert client.get(f"/api/v1/vehicles/{v['id']}", headers=h).json()["status"] == "available"
    hist = client.get(f"/api/v1/vehicles/{v['id']}/maintenance-records", headers=h).json()
    assert hist["total"] == 1 and hist["items"][0]["cost"] == 450.5


def test_preventive_schedule_rolls_forward_and_alerts(client):
    h = admin_headers(client)
    v = make_vehicle(client, h)
    s = client.post(f"{B}/schedules", json={"vehicle_id": v["id"], "description": "Oil change", "interval_days": 90,
                                           "last_service_date": (date.today() - timedelta(days=85)).isoformat()}, headers=h)
    assert s.status_code == 201
    assert client.post(f"{B}/due-check", headers=h).json()["notifications_created"] == 1  # one alert per due schedule
    assert client.post(f"{B}/due-check", headers=h).json()["notifications_created"] == 0  # idempotent
    req = client.post(f"{B}/requests", json={"vehicle_id": v["id"], "maintenance_type": "preventive", "description": "Oil change"}, headers=h).json()
    client.post(f"{B}/requests/{req['id']}/start", headers=h)
    client.post(f"{B}/requests/{req['id']}/complete", json={"cost": 50}, headers=h)
    nxt = client.get(f"{B}/vehicles/{v['id']}/schedules", headers=h).json()["items"][0]["next_due_date"]
    assert nxt == (date.today() + timedelta(days=90)).isoformat()


def test_cannot_service_vehicle_with_active_assignment(client, db):
    from tests.factories.flow import World
    w = World(client, db)
    w.assign()
    req = client.post(f"{B}/requests", json={"vehicle_id": w.vehicle["id"], "description": "Tyres"}, headers=w.h).json()
    assert client.post(f"{B}/requests/{req['id']}/start", headers=w.h).status_code == 422
