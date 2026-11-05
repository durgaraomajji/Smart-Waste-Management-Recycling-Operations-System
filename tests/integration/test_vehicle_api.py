from tests.factories.user_factory import admin_headers
from tests.factories.vehicle_factory import make_vehicle

B = "/api/v1/vehicles"


def test_register_normalises_and_blocks_duplicate(client):
    h = admin_headers(client)
    v = make_vehicle(client, h, reg="mh 12 ab 1234")
    assert v["registration_number"] == "MH12AB1234"
    r = client.post(B, json={"registration_number": "MH12AB1234", "vehicle_type": "tipper", "capacity_kg": 500, "fuel_type": "cng"}, headers=h)
    assert r.status_code == 409


def test_status_and_availability(client):
    h = admin_headers(client)
    v = make_vehicle(client, h)
    assert client.get(f"{B}/{v['id']}/availability", headers=h).json()["available"] is True
    client.patch(f"{B}/{v['id']}/status", json={"status": "under_maintenance"}, headers=h)
    a = client.get(f"{B}/{v['id']}/availability", headers=h).json()
    assert a["available"] is False and "under_maintenance" in a["reason"]
    # assigned/in_service cannot be set by hand
    assert client.patch(f"{B}/{v['id']}/status", json={"status": "assigned"}, headers=h).status_code == 422


def test_filters_and_capacity_validation(client):
    h = admin_headers(client)
    make_vehicle(client, h, reg="AA1111", capacity=500)
    make_vehicle(client, h, reg="BB2222", capacity=3000)
    assert client.get(f"{B}?min_capacity=1000", headers=h).json()["total"] == 1
    assert client.get(f"{B}?search=aa", headers=h).json()["total"] == 1
    bad = client.post(B, json={"registration_number": "CC3333", "vehicle_type": "tipper", "capacity_kg": -5, "fuel_type": "cng"}, headers=h)
    assert bad.status_code == 422
