from datetime import date, timedelta

from tests.factories.pickup_factory import approved_pickup, make_customer_with_address, make_pickup, tomorrow
from tests.factories.user_factory import PASSWORD, admin_headers, login
from tests.factories.waste_factory import category_id, make_zone

B = "/api/v1/pickup-requests"


def test_create_pickup_defaults_and_notifies(client, db):
    h = admin_headers(client)
    p = make_pickup(client, db, h)
    assert p["status"] == "pending" and p["request_no"].startswith("PR-")
    notes = client.get("/api/v1/notifications", headers=h).json()
    assert any(n["notification_type"] == "new_pickup_request" for n in notes["items"])


def test_past_date_and_zero_quantity_rejected(client, db):
    h = admin_headers(client)
    z = make_zone(client, h)
    c, a = make_customer_with_address(client, h, z["id"])
    base = {"customer_id": c["id"], "address_id": a["id"], "waste_category_id": category_id(db), "estimated_quantity_kg": 10}
    assert client.post(B, json={**base, "preferred_date": (date.today() - timedelta(days=1)).isoformat()}, headers=h).status_code == 422
    assert client.post(B, json={**base, "estimated_quantity_kg": 0, "preferred_date": tomorrow()}, headers=h).status_code == 422


def test_status_workflow_and_reject_needs_reason(client, db):
    h = admin_headers(client)
    p = make_pickup(client, db, h)
    assert client.patch(f"{B}/{p['id']}/status", json={"status": "rejected"}, headers=h).status_code == 400
    assert client.patch(f"{B}/{p['id']}/status", json={"status": "collected"}, headers=h).status_code == 400
    ok = client.patch(f"{B}/{p['id']}/status", json={"status": "rejected", "reason": "Out of area"}, headers=h)
    assert ok.status_code == 200 and ok.json()["status"] == "rejected"
    # terminal state
    assert client.patch(f"{B}/{p['id']}/status", json={"status": "approved"}, headers=h).status_code == 422


def test_cancel_pending_then_not_again(client, db):
    h = admin_headers(client)
    p = make_pickup(client, db, h)
    r = client.post(f"{B}/{p['id']}/cancel", json={"reason": "Not needed"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert client.post(f"{B}/{p['id']}/cancel", json={"reason": "Again"}, headers=h).status_code == 422


def test_customer_sees_only_own_requests(client, db):
    h = admin_headers(client)
    make_pickup(client, db, h)
    client.post("/api/v1/auth/register", json={"email": "own@example.com", "password": PASSWORD, "full_name": "Own Er"})
    mine = login(client, "own@example.com")
    assert client.get(B, headers=mine).json()["total"] == 0
    assert client.get(f"{B}/1", headers=mine).status_code == 403


def test_filters(client, db):
    h = admin_headers(client)
    approved_pickup(client, db, h)
    assert client.get(f"{B}?status=approved", headers=h).json()["total"] == 1
    assert client.get(f"{B}?status=pending", headers=h).json()["total"] == 0
    assert client.get(f"{B}?priority=medium&waste_category_id={category_id(db)}", headers=h).json()["total"] == 1
