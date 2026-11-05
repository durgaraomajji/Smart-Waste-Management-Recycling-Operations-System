from tests.factories.pickup_factory import make_customer_with_address
from tests.factories.user_factory import PASSWORD, admin_headers, login
from tests.factories.waste_factory import make_zone

B = "/api/v1/complaints"


def customer_session(client):
    client.post("/api/v1/auth/register", json={"email": "cc@example.com", "password": PASSWORD, "full_name": "Compl Ainer"})
    return login(client, "cc@example.com")


def test_complaint_lifecycle_and_history(client):
    cust = customer_session(client)
    h = admin_headers(client)
    r = client.post(B, json={"category": "missed_pickup", "description": "Nobody came on Tuesday", "priority": "high"}, headers=cust)
    assert r.status_code == 201
    cid = r.json()["id"]
    assert client.patch(f"{B}/{cid}/assign", json={"assigned_team": "Zone North"}, headers=h).json()["status"] == "assigned"
    assert client.patch(f"{B}/{cid}/status", json={"status": "resolved"}, headers=h).status_code == 400  # remarks needed
    ok = client.patch(f"{B}/{cid}/status", json={"status": "resolved", "remarks": "Re-collected"}, headers=h)
    assert ok.json()["resolution_remarks"] == "Re-collected"
    assert client.patch(f"{B}/{cid}/status", json={"status": "open"}, headers=h).status_code == 422
    hist = client.get(f"{B}/{cid}/history", headers=cust).json()
    assert [i["new_status"] for i in hist["items"]] == ["open", "assigned", "resolved"]
    mine = client.get("/api/v1/notifications", headers=cust).json()["items"]
    assert any("resolved" in n["title"].lower() for n in mine)


def test_customer_isolation_and_staff_filing(client):
    cust = customer_session(client)
    h = admin_headers(client)
    other = make_customer_with_address(client, h, make_zone(client, h)["id"])[0]
    c = client.post(B, json={"customer_id": other["id"], "category": "late_pickup", "description": "Arrived four hours late"}, headers=h).json()
    assert client.get(f"{B}/{c['id']}", headers=cust).status_code == 403
    assert client.get(B, headers=cust).json()["total"] == 0
    assert client.post(B, json={"category": "late_pickup", "description": "Arrived four hours late"}, headers=h).status_code == 400  # staff must name the customer
    assert client.patch(f"{B}/{c['id']}/assign", json={"assigned_team": "x"}, headers=cust).status_code == 403


def test_short_description_rejected(client):
    assert client.post(B, json={"category": "other", "description": "bad"}, headers=customer_session(client)).status_code == 422
