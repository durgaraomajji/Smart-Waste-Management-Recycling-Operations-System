from app.enums import UserRole
from tests.factories.pickup_factory import make_customer_with_address
from tests.factories.user_factory import PASSWORD, admin_headers, headers_for, login
from tests.factories.waste_factory import make_zone

B = "/api/v1/customers"


def test_customer_registration_addresses_and_filters(client):
    h = admin_headers(client)
    z = make_zone(client, h)
    c, addr = make_customer_with_address(client, h, z["id"])
    assert addr["is_default"] and addr["latitude"] == 18.52
    second = client.post(f"{B}/{c['id']}/addresses", json={"line1": "Office Rd 5", "city": "Pune", "is_default": True}, headers=h).json()
    got = client.get(f"{B}/{c['id']}", headers=h).json()
    defaults = [a["id"] for a in got["addresses"] if a["is_default"]]
    assert defaults == [second["id"]]
    assert client.get(f"{B}?search=asha", headers=h).json()["total"] == 1
    assert client.get(f"{B}?zone_id={z['id']}&service_status=active", headers=h).json()["total"] == 1
    assert client.get(f"{B}?service_status=suspended", headers=h).json()["total"] == 0


def test_invalid_coordinates_rejected(client):
    h = admin_headers(client)
    z = make_zone(client, h)
    c, _ = make_customer_with_address(client, h, z["id"])
    r = client.post(f"{B}/{c['id']}/addresses", json={"line1": "Bad Place", "city": "X", "latitude": 123}, headers=h)
    assert r.status_code == 422


def test_customer_cannot_view_another_customer(client):
    h = admin_headers(client)
    z = make_zone(client, h)
    other, _ = make_customer_with_address(client, h, z["id"])
    client.post("/api/v1/auth/register", json={"email": "me@example.com", "password": PASSWORD, "full_name": "Me Myself"})
    mine = login(client, "me@example.com")
    assert client.get(f"{B}/{other['id']}", headers=mine).status_code == 403
    assert client.get(f"{B}/me", headers=mine).status_code == 200
    assert client.get(B, headers=mine).status_code == 403
