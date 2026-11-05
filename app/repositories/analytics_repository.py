"""Aggregate queries used by analytics, reports and the dashboard.

All figures are in kilograms. Soft-deleted rows are always excluded.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums import (
    CollectionStatus,
    DisposalStatus,
    PickupStatus,
    ProcessingStatus,
)
from app.models import (
    CollectionAssignment,
    CollectionRecord,
    Driver,
    DisposalRecord,
    PickupRequest,
    ProcessingBatch,
    ServiceZone,
    Vehicle,
    WasteCategory,
    WasteSegregation,
)
from app.repositories.base_repository import day_end, day_start


@dataclass
class ReportFilters:
    date_from: date | None = None
    date_to: date | None = None
    zone_id: int | None = None
    waste_category_id: int | None = None


COLLECTED_STATES = (CollectionStatus.COMPLETED, CollectionStatus.INCOMPLETE)
DISPOSED_STATES = (DisposalStatus.APPROVED, DisposalStatus.DISPOSED)


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ filters
    @staticmethod
    def _pickup_f(stmt, f: ReportFilters):
        stmt = stmt.where(PickupRequest.is_deleted.is_(False))
        if f.date_from:
            stmt = stmt.where(PickupRequest.preferred_date >= f.date_from)
        if f.date_to:
            stmt = stmt.where(PickupRequest.preferred_date <= f.date_to)
        if f.zone_id:
            stmt = stmt.where(PickupRequest.zone_id == f.zone_id)
        if f.waste_category_id:
            stmt = stmt.where(PickupRequest.waste_category_id == f.waste_category_id)
        return stmt

    @staticmethod
    def _record_f(stmt, f: ReportFilters):
        """Filter collection records (joined to pickup_requests)."""
        stmt = stmt.where(CollectionRecord.is_deleted.is_(False))
        if f.date_from:
            stmt = stmt.where(CollectionRecord.created_at >= day_start(f.date_from))
        if f.date_to:
            stmt = stmt.where(CollectionRecord.created_at <= day_end(f.date_to))
        if f.zone_id:
            stmt = stmt.where(PickupRequest.zone_id == f.zone_id)
        if f.waste_category_id:
            stmt = stmt.where(PickupRequest.waste_category_id == f.waste_category_id)
        return stmt

    def _records(self, f: ReportFilters, *cols):
        stmt = select(*cols).select_from(CollectionRecord).join(PickupRequest, PickupRequest.id == CollectionRecord.pickup_request_id)
        return self._record_f(stmt, f)

    # ------------------------------------------------------------- pickups
    def pickup_status_counts(self, f: ReportFilters) -> dict[PickupStatus, int]:
        stmt = self._pickup_f(select(PickupRequest.status, func.count()).group_by(PickupRequest.status), f)
        return {s: c for s, c in self.db.execute(stmt).all()}

    def missed_count(self, f: ReportFilters) -> int:
        stmt = self._records(f, func.count()).where(CollectionRecord.status == CollectionStatus.MISSED)
        return self.db.scalar(stmt) or 0

    def collection_minutes(self, f: ReportFilters) -> list[float]:
        stmt = self._records(f, CollectionRecord.started_at, CollectionRecord.completed_at).where(
            CollectionRecord.status == CollectionStatus.COMPLETED,
            CollectionRecord.started_at.is_not(None),
            CollectionRecord.completed_at.is_not(None),
        )
        return [(c - s).total_seconds() / 60 for s, c in self.db.execute(stmt).all()]

    # ---------------------------------------------------------------- zone
    def zone_stats(self, f: ReportFilters) -> list[dict]:
        zones = {z.id: z.name for z in self.db.scalars(select(ServiceZone).where(ServiceZone.is_deleted.is_(False)))}
        by_zone: dict[int, dict] = defaultdict(lambda: {"total": 0, "completed": 0, "cancelled": 0, "missed": 0, "kg": 0.0})

        rows = self.db.execute(
            self._pickup_f(select(PickupRequest.zone_id, PickupRequest.status, func.count()).group_by(PickupRequest.zone_id, PickupRequest.status), f)
        ).all()
        for zid, status, cnt in rows:
            if zid is None:
                continue
            d = by_zone[zid]
            d["total"] += cnt
            if status == PickupStatus.COLLECTED:
                d["completed"] += cnt
            if status in (PickupStatus.CANCELLED, PickupStatus.REJECTED):
                d["cancelled"] += cnt

        recs = self.db.execute(
            self._records(f, PickupRequest.zone_id, CollectionRecord.status, func.count(), func.coalesce(func.sum(CollectionRecord.collected_quantity_kg), 0.0))
            .group_by(PickupRequest.zone_id, CollectionRecord.status)
        ).all()
        for zid, status, cnt, kg in recs:
            if zid is None:
                continue
            if status == CollectionStatus.MISSED:
                by_zone[zid]["missed"] += cnt
            if status in COLLECTED_STATES:
                by_zone[zid]["kg"] += float(kg or 0)

        out = []
        for zid, d in sorted(by_zone.items()):
            effective = d["total"] - d["cancelled"]
            out.append(
                {
                    "zone_id": zid,
                    "zone_name": zones.get(zid, f"Zone {zid}"),
                    "total_requests": d["total"],
                    "completed": d["completed"],
                    "missed": d["missed"],
                    "efficiency_pct": round(d["completed"] / effective * 100, 2) if effective else 0.0,
                    "total_collected_kg": round(d["kg"], 2),
                }
            )
        return out

    # -------------------------------------------------------------- driver
    def driver_stats(self, f: ReportFilters) -> list[dict]:
        names = {d.id: d.full_name for d in self.db.scalars(select(Driver).where(Driver.is_deleted.is_(False)))}
        stmt = (
            self._records(
                f,
                CollectionAssignment.driver_id,
                CollectionRecord.status,
                CollectionRecord.collected_quantity_kg,
                CollectionRecord.started_at,
                CollectionRecord.completed_at,
            ).join(CollectionAssignment, CollectionAssignment.id == CollectionRecord.assignment_id)
        )
        agg: dict[int, dict] = defaultdict(lambda: {"n": 0, "done": 0, "missed": 0, "kg": 0.0, "mins": []})
        for driver_id, status, kg, started, completed in self.db.execute(stmt).all():
            a = agg[driver_id]
            a["n"] += 1
            if status == CollectionStatus.COMPLETED:
                a["done"] += 1
                if started and completed:
                    a["mins"].append((completed - started).total_seconds() / 60)
            if status == CollectionStatus.MISSED:
                a["missed"] += 1
            if status in COLLECTED_STATES:
                a["kg"] += float(kg or 0)
        return [
            {
                "driver_id": did,
                "driver_name": names.get(did, f"Driver {did}"),
                "assignments": a["n"],
                "completed": a["done"],
                "missed": a["missed"],
                "efficiency_pct": round(a["done"] / a["n"] * 100, 2) if a["n"] else 0.0,
                "total_collected_kg": round(a["kg"], 2),
                "average_collection_time_minutes": round(sum(a["mins"]) / len(a["mins"]), 2) if a["mins"] else 0.0,
            }
            for did, a in sorted(agg.items())
        ]

    # ------------------------------------------------------------- vehicle
    def vehicle_stats(self, f: ReportFilters) -> list[dict]:
        vehicles = {v.id: v for v in self.db.scalars(select(Vehicle).where(Vehicle.is_deleted.is_(False)))}
        stmt = self._records(f, CollectionAssignment.vehicle_id, CollectionRecord.collected_quantity_kg).join(
            CollectionAssignment, CollectionAssignment.id == CollectionRecord.assignment_id
        ).where(CollectionRecord.status.in_(COLLECTED_STATES))
        agg: dict[int, dict] = defaultdict(lambda: {"trips": 0, "kg": 0.0})
        for vid, kg in self.db.execute(stmt).all():
            agg[vid]["trips"] += 1
            agg[vid]["kg"] += float(kg or 0)
        out = []
        for vid, a in sorted(agg.items()):
            v = vehicles.get(vid)
            cap = v.capacity_kg if v else 0.0
            out.append(
                {
                    "vehicle_id": vid,
                    "registration_number": v.registration_number if v else str(vid),
                    "capacity_kg": cap,
                    "trips": a["trips"],
                    "total_collected_kg": round(a["kg"], 2),
                    # average load factor: collected / (capacity x trips)
                    "utilization_pct": round(a["kg"] / (cap * a["trips"]) * 100, 2) if cap and a["trips"] else 0.0,
                }
            )
        return out

    # --------------------------------------------------------- environment
    def total_collected_kg(self, f: ReportFilters) -> float:
        stmt = self._records(f, func.coalesce(func.sum(CollectionRecord.collected_quantity_kg), 0.0)).where(
            CollectionRecord.status.in_(COLLECTED_STATES)
        )
        return float(self.db.scalar(stmt) or 0.0)

    def total_recyclable_kg(self, f: ReportFilters) -> float:
        stmt = select(func.coalesce(func.sum(WasteSegregation.recyclable_kg), 0.0)).where(WasteSegregation.is_deleted.is_(False))
        if f.date_from:
            stmt = stmt.where(WasteSegregation.created_at >= day_start(f.date_from))
        if f.date_to:
            stmt = stmt.where(WasteSegregation.created_at <= day_end(f.date_to))
        if f.waste_category_id:
            stmt = stmt.where(WasteSegregation.waste_category_id == f.waste_category_id)
        return float(self.db.scalar(stmt) or 0.0)

    def total_recycled_kg(self, f: ReportFilters) -> float:
        stmt = select(func.coalesce(func.sum(ProcessingBatch.recycled_output_kg), 0.0)).where(
            ProcessingBatch.is_deleted.is_(False), ProcessingBatch.status == ProcessingStatus.COMPLETED
        )
        if f.date_from:
            stmt = stmt.where(ProcessingBatch.processing_date >= f.date_from)
        if f.date_to:
            stmt = stmt.where(ProcessingBatch.processing_date <= f.date_to)
        if f.waste_category_id:
            stmt = stmt.where(ProcessingBatch.waste_category_id == f.waste_category_id)
        return float(self.db.scalar(stmt) or 0.0)

    def total_disposed_kg(self, f: ReportFilters) -> float:
        stmt = select(func.coalesce(func.sum(DisposalRecord.quantity_kg), 0.0)).where(
            DisposalRecord.is_deleted.is_(False), DisposalRecord.status.in_(DISPOSED_STATES)
        )
        if f.date_from:
            stmt = stmt.where(DisposalRecord.disposal_date >= f.date_from)
        if f.date_to:
            stmt = stmt.where(DisposalRecord.disposal_date <= f.date_to)
        if f.waste_category_id:
            stmt = stmt.where(DisposalRecord.waste_category_id == f.waste_category_id)
        return float(self.db.scalar(stmt) or 0.0)

    def category_distribution(self, f: ReportFilters) -> list[tuple[int, str, float]]:
        stmt = (
            self._records(f, PickupRequest.waste_category_id, WasteCategory.name, func.coalesce(func.sum(CollectionRecord.collected_quantity_kg), 0.0))
            .join(WasteCategory, WasteCategory.id == PickupRequest.waste_category_id)
            .where(CollectionRecord.status.in_(COLLECTED_STATES))
            .group_by(PickupRequest.waste_category_id, WasteCategory.name)
            .order_by(PickupRequest.waste_category_id)
        )
        return [(cid, name, float(kg or 0)) for cid, name, kg in self.db.execute(stmt).all()]

    def monthly_recycling(self, f: ReportFilters) -> list[dict]:
        stmt = select(ProcessingBatch.processing_date, ProcessingBatch.input_quantity_kg, ProcessingBatch.recycled_output_kg).where(
            ProcessingBatch.is_deleted.is_(False), ProcessingBatch.status == ProcessingStatus.COMPLETED
        )
        if f.date_from:
            stmt = stmt.where(ProcessingBatch.processing_date >= f.date_from)
        if f.date_to:
            stmt = stmt.where(ProcessingBatch.processing_date <= f.date_to)
        if f.waste_category_id:
            stmt = stmt.where(ProcessingBatch.waste_category_id == f.waste_category_id)
        months: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
        for d, inp, out in self.db.execute(stmt).all():
            key = f"{d:%Y-%m}"
            months[key][0] += inp
            months[key][1] += out
        return [
            {
                "month": m,
                "input_kg": round(v[0], 2),
                "recycled_kg": round(v[1], 2),
                "recycling_pct": round(v[1] / v[0] * 100, 2) if v[0] else 0.0,
            }
            for m, v in sorted(months.items())
        ]

    # ---------------------------------------------------------- report helpers
    def collection_rows(self, f: ReportFilters, status: CollectionStatus | None = None):
        stmt = self._records(f, CollectionRecord.created_at, CollectionRecord.status, CollectionRecord.collected_quantity_kg)
        if status:
            stmt = stmt.where(CollectionRecord.status == status)
        return self.db.execute(stmt).all()
