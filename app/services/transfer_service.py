from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, BusinessRuleError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import CenterStatus, CollectionStatus, TransferStatus, VehicleStatus
from app.models import CollectionRecord, PickupRequest, User, WasteTransfer
from app.models.base_model import utcnow
from app.repositories.location_repository import ZoneRepository
from app.repositories.recycling_center_repository import RecyclingCenterRepository
from app.repositories.transfer_repository import TransferRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.waste_category_repository import WasteCategoryRepository
from app.schemas.waste_transfer import TransferCreate
from app.services.audit_service import AuditService
from app.services.recycling_center_service import RecyclingCenterService, check_center_access
from app.services.vehicle_service import ASSIGNABLE
from app.utils.validators import get_or_404

TRANSITIONS = {
    TransferStatus.PENDING: {TransferStatus.IN_TRANSIT, TransferStatus.CANCELLED},
    TransferStatus.IN_TRANSIT: {TransferStatus.DELIVERED, TransferStatus.CANCELLED},
    TransferStatus.DELIVERED: set(),
    TransferStatus.CANCELLED: set(),
}


class TransferService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransferRepository(db)
        self.centers = RecyclingCenterRepository(db)
        self.vehicles = VehicleRepository(db)
        self.zones = ZoneRepository(db)
        self.categories = WasteCategoryRepository(db)
        self.center_service = RecyclingCenterService(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------------ stock
    def available_stock_kg(self, zone_id: int, category_id: int) -> float:
        """Collected waste in a zone/category that has not yet been committed to a transfer."""
        collected = self.db.scalar(
            select(func.coalesce(func.sum(CollectionRecord.collected_quantity_kg), 0.0))
            .join(PickupRequest, PickupRequest.id == CollectionRecord.pickup_request_id)
            .where(
                CollectionRecord.is_deleted.is_(False),
                CollectionRecord.status.in_((CollectionStatus.COMPLETED, CollectionStatus.INCOMPLETE)),
                PickupRequest.zone_id == zone_id,
                PickupRequest.waste_category_id == category_id,
            )
        )
        transferred = self.db.scalar(
            select(func.coalesce(func.sum(WasteTransfer.quantity_kg), 0.0)).where(
                WasteTransfer.is_deleted.is_(False),
                WasteTransfer.status != TransferStatus.CANCELLED,
                WasteTransfer.source_zone_id == zone_id,
                WasteTransfer.waste_category_id == category_id,
            )
        )
        return round(float(collected or 0) - float(transferred or 0), 2)

    # ------------------------------------------------------------------ create
    def create(self, actor: User, data: TransferCreate) -> WasteTransfer:
        get_or_404(self.zones, data.source_zone_id, "Source zone")
        category = get_or_404(self.categories, data.waste_category_id, "Waste category")
        center = get_or_404(self.centers, data.center_id, "Recycling center")
        vehicle = get_or_404(self.vehicles, data.vehicle_id, "Vehicle")

        if center.status != CenterStatus.ACTIVE:
            raise BusinessRuleError(f"Recycling center is not accepting waste (status: {center.status.value})")
        if not self.centers.accepts(center, category.id):
            raise BusinessRuleError(f"{center.name} does not accept {category.name}")
        free = center.daily_capacity_kg - center.current_load_kg
        if data.quantity_kg > free:
            raise BusinessRuleError(f"Center capacity exceeded - only {max(free, 0):.2f} kg free")
        if vehicle.status not in ASSIGNABLE:
            raise BusinessRuleError(f"Vehicle is not available (status: {vehicle.status.value})")
        if vehicle.capacity_kg < data.quantity_kg:
            raise BusinessRuleError(f"Quantity exceeds vehicle capacity ({vehicle.capacity_kg} kg)")
        stock = self.available_stock_kg(data.source_zone_id, category.id)
        if data.quantity_kg > stock:
            raise BusinessRuleError(f"Only {stock:.2f} kg of collected {category.name} is available in this zone")

        with transaction(self.db):
            t = self.repo.add(
                WasteTransfer(transfer_no=self.repo.next_number("TR"), initiated_by_id=actor.id, **data.model_dump())
            )
            self.audit.log(actor, "WASTE_TRANSFER_CREATED", "waste_transfer", t.id, {"kg": t.quantity_kg, "center_id": center.id})
        return t

    def get(self, transfer_id: int) -> WasteTransfer:
        return get_or_404(self.repo, transfer_id, "Waste transfer")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    # ------------------------------------------------------------ status change
    def update_status(self, actor: User, transfer_id: int, status: TransferStatus, remarks: str | None) -> WasteTransfer:
        t = self.get(transfer_id)
        center = self.centers.get(t.center_id)
        check_center_access(actor, center)
        if status not in TRANSITIONS[t.status]:
            raise BusinessRuleError(f"Cannot move a transfer from '{t.status.value}' to '{status.value}'")
        with transaction(self.db):
            old = t.status
            t.status = status
            if remarks:
                t.remarks = remarks
            if status == TransferStatus.IN_TRANSIT:
                t.dispatched_at = utcnow()
            elif status == TransferStatus.DELIVERED:
                free = center.daily_capacity_kg - center.current_load_kg
                if t.quantity_kg > free:
                    raise BusinessRuleError(f"Center capacity exceeded - only {max(free, 0):.2f} kg free")
                t.delivered_at = utcnow()
                center.current_load_kg = round(center.current_load_kg + t.quantity_kg, 2)
                self.center_service.raise_capacity_alert_if_needed(center)
            self.audit.log(
                actor, f"WASTE_TRANSFER_{status.value.upper()}", "waste_transfer", t.id, {"from": old.value, "kg": t.quantity_kg}
            )
        return t
