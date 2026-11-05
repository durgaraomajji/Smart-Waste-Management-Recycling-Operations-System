from tests.factories.user_factory import admin_headers

B = "/api/v1/waste-categories"


def test_seeded_categories_present(client):
    h = admin_headers(client)
    r = client.get(B, headers=h)
    names = {c["name"] for c in r.json()["items"]}
    assert {"Organic Waste", "Plastic Waste", "Paper Waste", "Metal Waste", "Glass Waste", "Electronic Waste", "Hazardous Waste"} <= names


def test_filter_by_recyclability_and_rules(client):
    h = admin_headers(client)
    haz = client.get(f"{B}?recyclability=hazardous", headers=h).json()
    assert haz["total"] == 1 and haz["items"][0]["is_hazardous"] and haz["items"][0]["segregation_rules"]


def test_create_duplicate_and_rule(client):
    h = admin_headers(client)
    body = {"name": "Textile Waste", "code": "txt", "recyclability": "partially_recyclable"}
    c = client.post(B, json=body, headers=h)
    assert c.status_code == 201 and c.json()["code"] == "TXT"
    assert client.post(B, json=body, headers=h).status_code == 409
    r = client.post(f"{B}/{c.json()['id']}/segregation-rules", json={"title": "Dry only", "description": "Keep textiles dry"}, headers=h)
    assert r.status_code == 201
