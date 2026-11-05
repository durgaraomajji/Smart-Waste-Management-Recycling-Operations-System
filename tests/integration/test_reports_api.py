from datetime import date, timedelta

from tests.factories.flow import World
from tests.integration.test_processing_api import batch
from tests.factories.waste_factory import category_id

B = "/api/v1/reports"


def finished(client, db):
    w, c, r = batch(client, db, 50)
    bid = r.json()["id"]
    client.post(f"/api/v1/processing/batches/{bid}/start", headers=w.h)
    client.post(f"/api/v1/processing/batches/{bid}/complete", json={"recycled_output_kg": 40, "processing_loss_kg": 10}, headers=w.h)
    return w, c


def test_every_report_runs(client, db):
    w, _ = finished(client, db)
    names = client.get(B, headers=w.h).json()["reports"]
    assert len(names) == 10
    for n in names:
        r = client.get(f"{B}/{n}", headers=w.h)
        assert r.status_code == 200, (n, r.text)
        assert r.json()["report"] == n


def test_daily_report_content_and_filters(client, db):
    w, _ = finished(client, db)
    rows = client.get(f"{B}/daily-collection", headers=w.h).json()["items"]
    assert rows[0]["completed"] == 1 and rows[0]["collected_kg"] == 90
    future = (date.today() + timedelta(days=5)).isoformat()
    assert client.get(f"{B}/daily-collection?date_from={future}", headers=w.h).json()["total"] == 0
    assert client.get(f"{B}/daily-collection?zone_id=999", headers=w.h).json()["total"] == 0
    assert client.get(f"{B}/daily-collection?date_from=2030-02-01&date_to=2030-01-01", headers=w.h).status_code == 400


def test_recycling_yield_report_and_status_filter(client, db):
    w, _ = finished(client, db)
    rows = client.get(f"{B}/recycling-yield", headers=w.h).json()["items"]
    assert rows[0]["yield_pct"] == 80.0
    assert client.get(f"{B}/recycling-yield?status=failed", headers=w.h).json()["total"] == 0
    assert client.get(f"{B}/recycling-yield?status=bogus", headers=w.h).status_code == 400


def test_sorting_pagination_and_unknown_report(client, db):
    w, _ = finished(client, db)
    assert client.get(f"{B}/nope", headers=w.h).status_code == 400
    assert client.get(f"{B}/waste-category?sort_by=nope", headers=w.h).status_code == 400
    r = client.get(f"{B}/environmental-impact?sort_by=value&order=desc&page=1&page_size=2", headers=w.h).json()
    assert len(r["items"]) == 2 and r["total"] > 2
    assert r["items"][0]["value"] >= r["items"][1]["value"]


def test_csv_export(client, db):
    w, _ = finished(client, db)
    r = client.get(f"{B}/zone-performance/export", headers=w.h)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0].startswith("zone_id,zone_name") and len(lines) == 2
    assert "zone-performance.csv" in r.headers["content-disposition"]


def test_analytics_endpoints(client, db):
    w, _ = finished(client, db)
    perf = client.get("/api/v1/analytics/collection-performance", headers=w.h).json()
    assert perf["total_pickup_requests"] == 1 and perf["completed_pickups"] == 1 and perf["collection_efficiency_pct"] == 100.0
    veh = client.get("/api/v1/analytics/vehicles", headers=w.h).json()
    assert veh[0]["utilization_pct"] == 9.0  # 90 kg on a 1000 kg vehicle, 1 trip
    drv = client.get("/api/v1/analytics/drivers", headers=w.h).json()
    assert drv[0]["completed"] == 1 and drv[0]["total_collected_kg"] == 90
    env = client.get("/api/v1/analytics/environmental-impact", headers=w.h).json()
    assert env["recycling_percentage"] == round(40 / 90 * 100, 2)
    assert env["category_distribution"][0]["percentage"] == 100.0
    assert env["monthly_trends"][0]["recycling_pct"] == 80.0 and "recycling_percentage" in env["formulas"]
