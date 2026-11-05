from app.enums import UserRole
from tests.factories.user_factory import admin_headers, create_user
from tests.factories.waste_factory import make_zone

B = "/api/v1/locations"


def test_zone_area_street_schedule_flow(client):
    h = admin_headers(client)
    zone = make_zone(client, h)
    area = client.post(f"{B}/areas", json={"zone_id": zone["id"], "name": "Ward 1"}, headers=h)
    assert area.status_code == 201
    st = client.post(f"{B}/areas/{area.json()['id']}/streets", json={"name": "MG Road", "locality": "Central"}, headers=h)
    assert st.status_code == 201
    assert client.post(f"{B}/areas/{area.json()['id']}/streets", json={"name": "MG Road", "locality": "Central"}, headers=h).status_code == 409
    sched = client.post(f"{B}/schedules", json={"zone_id": zone["id"], "day_of_week": 2, "start_time": "08:00", "end_time": "12:00"}, headers=h)
    assert sched.status_code == 201
    bad = client.post(f"{B}/schedules", json={"zone_id": zone["id"], "day_of_week": 2, "start_time": "12:00", "end_time": "08:00"}, headers=h)
    assert bad.status_code == 422


def test_duplicate_zone_and_status_filter(client):
    h = admin_headers(client)
    z = make_zone(client, h)
    assert client.post(f"{B}/zones", json={"name": "North Zone", "code": "ZZ"}, headers=h).status_code == 409
    client.patch(f"{B}/zones/{z['id']}/status", json={"status": "suspended"}, headers=h)
    assert client.get(f"{B}/zones?status=suspended", headers=h).json()["total"] == 1
    assert client.get(f"{B}/zones?status=active", headers=h).json()["total"] == 0
    assert client.get(f"{B}/zones?search=north", headers=h).json()["total"] == 1


def test_assign_supervisor_requires_supervisor_role(client, db):
    h = admin_headers(client)
    z = make_zone(client, h)
    cust = create_user(db, UserRole.CUSTOMER, "cu@example.com")
    sup = create_user(db, UserRole.COLLECTION_SUPERVISOR, "sup@example.com")
    assert client.put(f"{B}/zones/{z['id']}/supervisor", json={"supervisor_id": cust.id}, headers=h).status_code == 400
    r = client.put(f"{B}/zones/{z['id']}/supervisor", json={"supervisor_id": sup.id}, headers=h)
    assert r.status_code == 200 and r.json()["supervisor_id"] == sup.id
