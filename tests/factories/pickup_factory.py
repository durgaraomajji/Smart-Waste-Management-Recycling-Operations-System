import itertools
from datetime import date, datetime, timedelta

from tests.factories.user_factory import admin_headers
from tests.factories.waste_factory import category_id, make_zone


def tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def slot(hours: int = 24) -> str:
    return (datetime.utcnow() + timedelta(hours=hours)).replace(microsecond=0).isoformat()


_counter = itertools.count(1)


def make_customer_with_address(client, headers, zone_id, unique: bool = False) -> tuple[dict, dict]:
    n = next(_counter) if unique else 0
    email = f"asha{n}@example.com" if n else "asha@example.com"
    r = client.post(
        "/api/v1/customers",
        json={"full_name": "Asha Patel", "email": email, "phone": "9000000001", "zone_id": zone_id,
              "address": {"line1": "12 Park Street", "city": "Pune", "latitude": 18.52, "longitude": 73.85}},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    customer = r.json()
    return customer, customer["addresses"][0]


def make_pickup(client, db, headers, qty=100.0, zone=None, code="PLS") -> dict:
    zone = zone or make_zone(client, headers)
    customer, address = make_customer_with_address(client, headers, zone["id"], unique=True)
    r = client.post(
        "/api/v1/pickup-requests",
        json={"customer_id": customer["id"], "address_id": address["id"], "waste_category_id": category_id(db, code),
              "estimated_quantity_kg": qty, "preferred_date": tomorrow()},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def approved_pickup(client, db, headers, qty=100.0, zone=None, code="PLS") -> dict:
    p = make_pickup(client, db, headers, qty, zone, code)
    r = client.patch(f"/api/v1/pickup-requests/{p['id']}/status", json={"status": "approved"}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()
