from datetime import date

from tests.integration.test_segregation_api import delivered
from tests.factories.waste_factory import category_id

B = "/api/v1/processing/batches"


def batch(client, db, kg=50):
    w, c, _ = delivered(client, db)
    r = client.post(B, json={"center_id": c["id"], "waste_category_id": category_id(db, "PLS"), "input_quantity_kg": kg, "processing_date": date.today().isoformat()}, headers=w.h)
    return w, c, r


def test_yield_is_calculated_on_completion(client, db):
    w, c, r = batch(client, db, 50)
    assert r.status_code == 201
    bid = r.json()["id"]
    assert client.get(f"/api/v1/recycling-centers/{c['id']}", headers=w.h).json()["current_load_kg"] == 30  # 80 - 50 reserved
    assert client.post(f"{B}/{bid}/complete", json={"recycled_output_kg": 40, "processing_loss_kg": 10}, headers=w.h).status_code == 422  # not started
    assert client.post(f"{B}/{bid}/start", headers=w.h).json()["status"] == "in_progress"
    done = client.post(f"{B}/{bid}/complete", json={"recycled_output_kg": 40, "processing_loss_kg": 10}, headers=w.h).json()
    assert done["status"] == "completed" and done["yield_percentage"] == 80.0


def test_output_plus_loss_cannot_exceed_input(client, db):
    w, c, r = batch(client, db, 50)
    bid = r.json()["id"]
    client.post(f"{B}/{bid}/start", headers=w.h)
    assert client.post(f"{B}/{bid}/complete", json={"recycled_output_kg": 45, "processing_loss_kg": 10}, headers=w.h).status_code == 422


def test_input_cannot_exceed_center_stock(client, db):
    w, c, r = batch(client, db, 500)
    assert r.status_code == 422


def test_failed_batch_returns_stock(client, db):
    w, c, r = batch(client, db, 50)
    assert client.post(f"{B}/{r.json()['id']}/fail", headers=w.h).json()["status"] == "failed"
    assert client.get(f"/api/v1/recycling-centers/{c['id']}", headers=w.h).json()["current_load_kg"] == 80
