"""Builds an end-to-end operational chain so integration tests stay short."""
from tests.factories.pickup_factory import approved_pickup, slot
from tests.factories.user_factory import admin_headers
from tests.factories.vehicle_factory import make_driver, make_vehicle, make_worker
from tests.factories.waste_factory import make_zone


class World:
    def __init__(self, client, db, qty=100.0, capacity=1000.0, code="PLS"):
        self.client, self.db = client, db
        self.h = admin_headers(client)
        self.zone = make_zone(client, self.h)
        self.pickup = approved_pickup(client, db, self.h, qty, self.zone, code)
        self.vehicle = make_vehicle(client, self.h, capacity=capacity)
        self.driver = make_driver(client, self.h)
        self.worker = make_worker(client, self.h)

    def assign(self, hours=24, expect=201, **over):
        body = {
            "pickup_request_id": self.pickup["id"], "driver_id": self.driver["id"], "vehicle_id": self.vehicle["id"],
            "worker_ids": [self.worker["id"]], "scheduled_at": slot(hours),
        }
        body.update(over)
        r = self.client.post("/api/v1/assignments", json=body, headers=self.h)
        assert r.status_code == expect, r.text
        self.assignment = r.json()
        return r

    def start(self):
        r = self.client.post("/api/v1/collections/start", json={"assignment_id": self.assignment["id"]}, headers=self.h)
        assert r.status_code == 201, r.text
        self.record = r.json()
        return r

    def complete(self, kg=90.0, expect=200):
        r = self.client.post(
            f"/api/v1/collections/{self.record['id']}/complete",
            json={"collected_quantity_kg": kg, "remarks": "ok", "photo_urls": ["https://img.example.com/a.jpg"]},
            headers=self.h,
        )
        assert r.status_code == expect, r.text
        return r

    def collected(self, kg=90.0):
        self.assign()
        self.start()
        self.complete(kg)
        return self

    def center(self, capacity=5000.0, code="RC1", categories=None):
        from tests.factories.waste_factory import category_id

        cats = categories or [category_id(self.db, "PLS")]
        r = self.client.post(
            "/api/v1/recycling-centers",
            json={"name": f"Center {code}", "code": code, "address": "Industrial Estate", "daily_capacity_kg": capacity, "accepted_category_ids": cats},
            headers=self.h,
        )
        assert r.status_code == 201, r.text
        return r.json()
