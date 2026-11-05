from tests.factories.user_factory import admin_headers
from tests.factories.vehicle_factory import make_driver, make_worker

B = "/api/v1/workforce"


def test_driver_validation_and_duplicates(client):
    h = admin_headers(client)
    make_driver(client, h)
    dup = client.post(f"{B}/drivers", json={"employee_code": "DRV2", "full_name": "Other", "phone": "9876543211", "license_number": "LIC-001", "license_expiry": "2099-01-01"}, headers=h)
    assert dup.status_code == 409
    expired = client.post(f"{B}/drivers", json={"employee_code": "DRV3", "full_name": "Old Lic", "phone": "9876543212", "license_number": "LIC-9", "license_expiry": "2000-01-01"}, headers=h)
    assert expired.status_code == 422


def test_worker_status_and_filter(client):
    h = admin_headers(client)
    w = make_worker(client, h)
    client.patch(f"{B}/workers/{w['id']}/status", json={"status": "on_leave"}, headers=h)
    assert client.get(f"{B}/workers?status=on_leave", headers=h).json()["total"] == 1
    assert client.patch(f"{B}/workers/{w['id']}/status", json={"status": "assigned"}, headers=h).status_code == 400


def test_history_starts_empty(client):
    h = admin_headers(client)
    d = make_driver(client, h)
    assert client.get(f"{B}/drivers/{d['id']}/history", headers=h).json()["total"] == 0
