from tests.factories.flow import World
from tests.factories.waste_factory import category_id

B = "/api/v1/segregation"


def delivered(client, db, kg=90, move=80):
    w = World(client, db).collected(kg)
    c = w.center()
    t = client.post("/api/v1/transfers", json={"source_zone_id": w.zone["id"], "center_id": c["id"], "waste_category_id": category_id(db, "PLS"),
                                              "quantity_kg": move, "vehicle_id": w.vehicle["id"]}, headers=w.h).json()
    for s in ("in_transit", "delivered"):
        client.patch(f"/api/v1/transfers/{t['id']}/status", json={"status": s}, headers=w.h)
    return w, c, t


def test_record_segregation(client, db):
    w, c, t = delivered(client, db)
    r = client.post(B, json={"transfer_id": t["id"], "center_id": c["id"], "waste_category_id": category_id(db, "PLS"),
                             "incoming_quantity_kg": 80, "recyclable_kg": 60, "non_recyclable_kg": 15, "contaminated_kg": 5}, headers=w.h)
    assert r.status_code == 201
    assert client.get(f"{B}?center_id={c['id']}", headers=w.h).json()["total"] == 1


def test_components_cannot_exceed_incoming(client, db):
    w, c, t = delivered(client, db)
    r = client.post(B, json={"center_id": c["id"], "waste_category_id": category_id(db, "PLS"),
                             "incoming_quantity_kg": 50, "recyclable_kg": 40, "non_recyclable_kg": 20}, headers=w.h)
    assert r.status_code == 422


def test_cannot_segregate_more_than_transfer(client, db):
    w, c, t = delivered(client, db)
    base = {"transfer_id": t["id"], "center_id": c["id"], "waste_category_id": category_id(db, "PLS"), "recyclable_kg": 10, "non_recyclable_kg": 0}
    assert client.post(B, json={**base, "incoming_quantity_kg": 50}, headers=w.h).status_code == 201
    assert client.post(B, json={**base, "incoming_quantity_kg": 50}, headers=w.h).status_code == 422
