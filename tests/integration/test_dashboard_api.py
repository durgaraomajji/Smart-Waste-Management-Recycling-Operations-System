from tests.factories.flow import World
from tests.integration.test_processing_api import batch
from tests.factories.user_factory import admin_headers

B = "/api/v1/dashboard"


def test_empty_dashboard(client):
    d = client.get(B, headers=admin_headers(client)).json()
    assert d["total_customers"] == 0 and d["recycling_efficiency_pct"] == 0.0 and d["total_waste_collected_kg"] == 0


def test_dashboard_metrics_after_full_flow(client, db):
    w, c, r = batch(client, db, 50)  # collected 90kg, delivered 80kg, batch of 50kg
    bid = r.json()["id"]
    client.post(f"/api/v1/processing/batches/{bid}/start", headers=w.h)
    client.post(f"/api/v1/processing/batches/{bid}/complete", json={"recycled_output_kg": 40, "processing_loss_kg": 10}, headers=w.h)
    d = client.get(B, headers=w.h).json()
    assert d["total_customers"] == 1
    assert d["total_collection_requests"] == 1 and d["completed_collections"] == 1 and d["pending_pickups"] == 0
    assert d["total_vehicles"] == 1 and d["available_vehicles"] == 1
    assert d["active_recycling_centers"] == 1
    assert d["total_waste_collected_kg"] == 90 and d["total_waste_recycled_kg"] == 40
    assert d["recycling_efficiency_pct"] == round(40 / 90 * 100, 2)


def test_dashboard_counts_missed_and_pending(client, db):
    w = World(client, db)
    w.assign()
    w.start()
    client.post(f"/api/v1/collections/{w.record['id']}/incomplete", json={"reason": "Locked", "missed": True}, headers=w.h)
    d = client.get(B, headers=w.h).json()
    assert d["missed_collections"] == 1 and d["pending_pickups"] == 1 and d["completed_collections"] == 0


def test_dashboard_forbidden_for_customers(client):
    from tests.factories.user_factory import PASSWORD, login
    client.post("/api/v1/auth/register", json={"email": "d@example.com", "password": PASSWORD, "full_name": "Dash Board"})
    assert client.get(B, headers=login(client, "d@example.com")).status_code == 403
