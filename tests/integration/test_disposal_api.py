from datetime import date

from app.enums import UserRole
from tests.integration.test_segregation_api import delivered
from tests.factories.user_factory import create_user, login
from tests.factories.waste_factory import category_id

B = "/api/v1/disposals"


def create(client, db, kg=20):
    w, c, _ = delivered(client, db)
    # a centre manager raises the disposal; the admin approves it
    mgr = create_user(db, UserRole.RECYCLING_CENTER_MANAGER, "dm@example.com")
    client.put(f"/api/v1/recycling-centers/{c['id']}/manager", json={"manager_id": mgr.id}, headers=w.h)
    mh = login(client, "dm@example.com")
    r = client.post(B, json={"center_id": c["id"], "waste_category_id": category_id(db, "PLS"), "method": "landfill",
                             "quantity_kg": kg, "location": "City landfill", "disposal_date": date.today().isoformat()}, headers=mh)
    return w, c, mh, r


def test_disposal_approval_reduces_center_stock(client, db):
    w, c, mh, r = create(client, db)
    assert r.status_code == 201 and r.json()["status"] == "pending_approval"
    did = r.json()["id"]
    assert client.post(f"{B}/{did}/decision", json={"approve": True}, headers=mh).status_code == 403  # manager cannot approve
    ok = client.post(f"{B}/{did}/decision", json={"approve": True, "remarks": "fine"}, headers=w.h)
    assert ok.status_code == 200 and ok.json()["status"] == "approved" and ok.json()["approved_by_id"]
    assert client.get(f"/api/v1/recycling-centers/{c['id']}", headers=w.h).json()["current_load_kg"] == 60
    assert client.post(f"{B}/{did}/decision", json={"approve": False}, headers=w.h).status_code == 422  # already decided
    assert client.post(f"{B}/{did}/complete", headers=mh).json()["status"] == "disposed"


def test_rejection_keeps_stock_and_cannot_complete(client, db):
    w, c, mh, r = create(client, db)
    did = r.json()["id"]
    assert client.post(f"{B}/{did}/decision", json={"approve": False, "remarks": "no"}, headers=w.h).json()["status"] == "rejected"
    assert client.get(f"/api/v1/recycling-centers/{c['id']}", headers=w.h).json()["current_load_kg"] == 80
    assert client.post(f"{B}/{did}/complete", headers=mh).status_code == 422


def test_quantity_above_stock_rejected(client, db):
    w, c, mh, r = create(client, db, kg=500)
    assert r.status_code == 422


def test_responsible_person_cannot_self_approve(client, db):
    w, c, mh, r = create(client, db)
    # admin raises and tries to approve their own disposal
    own = client.post(B, json={"center_id": c["id"], "waste_category_id": category_id(db, "PLS"), "method": "landfill", "quantity_kg": 5,
                               "location": "Landfill", "disposal_date": date.today().isoformat()}, headers=w.h).json()
    assert client.post(f"{B}/{own['id']}/decision", json={"approve": True}, headers=w.h).status_code == 403
