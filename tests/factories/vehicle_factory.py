def make_vehicle(client, headers, reg="MH12AB1234", capacity=1000.0) -> dict:
    r = client.post(
        "/api/v1/vehicles",
        json={"registration_number": reg, "vehicle_type": "tipper", "capacity_kg": capacity, "fuel_type": "diesel"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def make_driver(client, headers, code="DRV1", license_no="LIC-001") -> dict:
    r = client.post(
        "/api/v1/workforce/drivers",
        json={"employee_code": code, "full_name": "Ravi Kumar", "phone": "9876543210", "license_number": license_no, "license_expiry": "2099-01-01"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def make_worker(client, headers, code="WRK1") -> dict:
    r = client.post(
        "/api/v1/workforce/workers",
        json={"employee_code": code, "full_name": "Sita Devi", "phone": "9876500000"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()
