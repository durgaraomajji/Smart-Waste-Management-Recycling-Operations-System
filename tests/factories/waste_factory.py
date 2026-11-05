from app.models import WasteCategory


def category_id(db, code: str = "PLS") -> int:
    return db.query(WasteCategory).filter_by(code=code).one().id


def make_zone(client, headers, code="Z1", name="North Zone") -> dict:
    r = client.post("/api/v1/locations/zones", json={"name": name, "code": code}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
