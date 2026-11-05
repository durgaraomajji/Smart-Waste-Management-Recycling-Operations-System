from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.core.pagination import PageParams
from app.enums import CollectionStatus, DisposalStatus, ProcessingStatus, TransferStatus
from app.models import DisposalRecord, ProcessingBatch, RecyclingCenter, WasteCategory, WasteTransfer
from app.repositories.analytics_repository import COLLECTED_STATES, AnalyticsRepository, ReportFilters
from app.services.analytics_service import AnalyticsService
from app.utils.calculation_utils import center_utilization, percentage, recycling_yield

REPORTS = (
    "daily-collection",
    "monthly-collection",
    "zone-performance",
    "driver-performance",
    "vehicle-utilization",
    "waste-category",
    "recycling-center-performance",
    "recycling-yield",
    "disposal",
    "environmental-impact",
)


class ReportService:
    """Builds tabular report rows; sorting, pagination and CSV export are handled uniformly here."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)
        self.analytics = AnalyticsService(db)

    # ------------------------------------------------------------------ public
    def generate(
        self,
        report: str,
        f: ReportFilters,
        status: str | None = None,
        sort_by: str | None = None,
        order: str = "asc",
        params: PageParams | None = None,
    ) -> dict:
        rows = self.rows(report, f, status)
        rows = self._sort(rows, sort_by, order)
        total = len(rows)
        if params:
            rows = rows[params.offset : params.offset + params.page_size]
        return {
            "report": report,
            "generated_for": {
                "date_from": f.date_from.isoformat() if f.date_from else None,
                "date_to": f.date_to.isoformat() if f.date_to else None,
                "zone_id": f.zone_id,
                "waste_category_id": f.waste_category_id,
                "status": status,
            },
            "total": total,
            "page": params.page if params else 1,
            "page_size": params.page_size if params else total,
            "items": rows,
        }

    def rows(self, report: str, f: ReportFilters, status: str | None = None) -> list[dict]:
        builders = {
            "daily-collection": lambda: self._collection_by_period(f, status, "%Y-%m-%d"),
            "monthly-collection": lambda: self._collection_by_period(f, status, "%Y-%m"),
            "zone-performance": lambda: self.analytics_repo.zone_stats(f),
            "driver-performance": lambda: self.analytics_repo.driver_stats(f),
            "vehicle-utilization": lambda: self.analytics_repo.vehicle_stats(f),
            "waste-category": lambda: self._waste_category(f),
            "recycling-center-performance": lambda: self._center_performance(f),
            "recycling-yield": lambda: self._recycling_yield(f, status),
            "disposal": lambda: self._disposal(f, status),
            "environmental-impact": lambda: self._environmental(f),
        }
        if report not in builders:
            raise BadRequestError(f"Unknown report '{report}'. Available: {', '.join(REPORTS)}")
        return builders[report]()

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _parse_status(enum_cls, status: str | None):
        if not status:
            return None
        try:
            return enum_cls(status)
        except ValueError:
            raise BadRequestError(f"Invalid status '{status}'. Allowed: {', '.join(e.value for e in enum_cls)}")

    @staticmethod
    def _sort(rows: list[dict], sort_by: str | None, order: str) -> list[dict]:
        if not sort_by or not rows:
            return rows
        if sort_by not in rows[0]:
            raise BadRequestError(f"Cannot sort by '{sort_by}'. Available columns: {', '.join(rows[0].keys())}")
        return sorted(rows, key=lambda r: (r[sort_by] is None, r[sort_by]), reverse=(order == "desc"))

    # ----------------------------------------------------------------- reports
    def _collection_by_period(self, f, status, fmt) -> list[dict]:
        st = self._parse_status(CollectionStatus, status)
        buckets: dict[str, dict] = defaultdict(lambda: {"total": 0, "completed": 0, "incomplete": 0, "missed": 0, "kg": 0.0})
        for created, s, kg in self.analytics_repo.collection_rows(f, st):
            b = buckets[created.strftime(fmt)]
            b["total"] += 1
            if s == CollectionStatus.COMPLETED:
                b["completed"] += 1
            elif s == CollectionStatus.INCOMPLETE:
                b["incomplete"] += 1
            elif s == CollectionStatus.MISSED:
                b["missed"] += 1
            if s in COLLECTED_STATES:
                b["kg"] += float(kg or 0)
        key = "date" if fmt == "%Y-%m-%d" else "month"
        return [
            {
                key: k,
                "total_collections": v["total"],
                "completed": v["completed"],
                "incomplete": v["incomplete"],
                "missed": v["missed"],
                "collected_kg": round(v["kg"], 2),
                "success_rate_pct": percentage(v["completed"], v["total"]),
            }
            for k, v in sorted(buckets.items())
        ]

    def _waste_category(self, f) -> list[dict]:
        dist = self.analytics_repo.category_distribution(f)
        total = sum(kg for _, _, kg in dist)
        return [
            {"category_id": cid, "category": name, "collected_kg": round(kg, 2), "share_pct": percentage(kg, total)} for cid, name, kg in dist
        ]

    def _center_performance(self, f) -> list[dict]:
        centers = self.db.scalars(select(RecyclingCenter).where(RecyclingCenter.is_deleted.is_(False)).order_by(RecyclingCenter.name)).all()
        out = []
        for c in centers:
            b = select(
                func.count(),
                func.coalesce(func.sum(ProcessingBatch.input_quantity_kg), 0.0),
                func.coalesce(func.sum(ProcessingBatch.recycled_output_kg), 0.0),
            ).where(
                ProcessingBatch.center_id == c.id, ProcessingBatch.is_deleted.is_(False), ProcessingBatch.status == ProcessingStatus.COMPLETED
            )
            t = select(func.coalesce(func.sum(WasteTransfer.quantity_kg), 0.0)).where(
                WasteTransfer.center_id == c.id, WasteTransfer.is_deleted.is_(False), WasteTransfer.status == TransferStatus.DELIVERED
            )
            if f.date_from:
                b = b.where(ProcessingBatch.processing_date >= f.date_from)
            if f.date_to:
                b = b.where(ProcessingBatch.processing_date <= f.date_to)
            if f.waste_category_id:
                b = b.where(ProcessingBatch.waste_category_id == f.waste_category_id)
                t = t.where(WasteTransfer.waste_category_id == f.waste_category_id)
            if f.zone_id:
                t = t.where(WasteTransfer.source_zone_id == f.zone_id)
            batches, inp, outp = self.db.execute(b).one()
            received = self.db.scalar(t)
            out.append(
                {
                    "center_id": c.id,
                    "center": c.name,
                    "status": c.status.value,
                    "daily_capacity_kg": c.daily_capacity_kg,
                    "current_load_kg": c.current_load_kg,
                    "utilization_pct": center_utilization(c.current_load_kg, c.daily_capacity_kg),
                    "received_kg": round(float(received or 0), 2),
                    "batches_completed": batches,
                    "processed_input_kg": round(float(inp), 2),
                    "recycled_output_kg": round(float(outp), 2),
                    "average_yield_pct": recycling_yield(float(outp), float(inp)),
                }
            )
        return out

    def _recycling_yield(self, f, status) -> list[dict]:
        st = self._parse_status(ProcessingStatus, status) or ProcessingStatus.COMPLETED
        stmt = (
            select(ProcessingBatch, RecyclingCenter.name, WasteCategory.name)
            .join(RecyclingCenter, RecyclingCenter.id == ProcessingBatch.center_id)
            .join(WasteCategory, WasteCategory.id == ProcessingBatch.waste_category_id)
            .where(ProcessingBatch.is_deleted.is_(False), ProcessingBatch.status == st)
            .order_by(ProcessingBatch.processing_date, ProcessingBatch.id)
        )
        if f.date_from:
            stmt = stmt.where(ProcessingBatch.processing_date >= f.date_from)
        if f.date_to:
            stmt = stmt.where(ProcessingBatch.processing_date <= f.date_to)
        if f.waste_category_id:
            stmt = stmt.where(ProcessingBatch.waste_category_id == f.waste_category_id)
        return [
            {
                "batch_no": b.batch_no,
                "processing_date": b.processing_date.isoformat(),
                "center": center,
                "category": cat,
                "status": b.status.value,
                "input_kg": b.input_quantity_kg,
                "recycled_output_kg": b.recycled_output_kg,
                "processing_loss_kg": b.processing_loss_kg,
                "yield_pct": b.yield_percentage,
            }
            for b, center, cat in self.db.execute(stmt).all()
        ]

    def _disposal(self, f, status) -> list[dict]:
        st = self._parse_status(DisposalStatus, status)
        stmt = (
            select(DisposalRecord, WasteCategory.name)
            .join(WasteCategory, WasteCategory.id == DisposalRecord.waste_category_id)
            .where(DisposalRecord.is_deleted.is_(False))
            .order_by(DisposalRecord.disposal_date, DisposalRecord.id)
        )
        if st:
            stmt = stmt.where(DisposalRecord.status == st)
        if f.date_from:
            stmt = stmt.where(DisposalRecord.disposal_date >= f.date_from)
        if f.date_to:
            stmt = stmt.where(DisposalRecord.disposal_date <= f.date_to)
        if f.waste_category_id:
            stmt = stmt.where(DisposalRecord.waste_category_id == f.waste_category_id)
        return [
            {
                "disposal_no": d.disposal_no,
                "disposal_date": d.disposal_date.isoformat(),
                "category": cat,
                "method": d.method.value,
                "quantity_kg": d.quantity_kg,
                "location": d.location,
                "status": d.status.value,
            }
            for d, cat in self.db.execute(stmt).all()
        ]

    def _environmental(self, f) -> list[dict]:
        impact = self.analytics.environmental_impact(f)
        rows = [
            {"metric": "total_waste_collected_kg", "value": impact.total_waste_collected_kg},
            {"metric": "total_recyclable_kg", "value": impact.total_recyclable_kg},
            {"metric": "total_waste_recycled_kg", "value": impact.total_recycled_kg},
            {"metric": "total_waste_disposed_kg", "value": impact.total_disposed_kg},
            {"metric": "recycling_percentage", "value": impact.recycling_percentage},
        ]
        rows += [{"metric": f"collected_kg:{c.category_name}", "value": c.collected_kg} for c in impact.category_distribution]
        rows += [{"metric": f"recycling_pct:{m.month}", "value": m.recycling_pct} for m in impact.monthly_trends]
        return rows
