from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import TransferStatus
from app.models import User, WasteSegregation
from app.repositories.recycling_center_repository import RecyclingCenterRepository
from app.repositories.segregation_repository import SegregationRepository
from app.repositories.transfer_repository import TransferRepository
from app.repositories.waste_category_repository import WasteCategoryRepository
from app.schemas.waste_segregation import SegregationCreate
from app.services.audit_service import AuditService
from app.services.recycling_center_service import check_center_access
from app.utils.validators import get_or_404


class SegregationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SegregationRepository(db)
        self.centers = RecyclingCenterRepository(db)
        self.transfers = TransferRepository(db)
        self.categories = WasteCategoryRepository(db)
        self.audit = AuditService(db)

    def create(self, actor: User, data: SegregationCreate) -> WasteSegregation:
        center = get_or_404(self.centers, data.center_id, "Recycling center")
        check_center_access(actor, center)
        get_or_404(self.categories, data.waste_category_id, "Waste category")

        if data.transfer_id:
            t = get_or_404(self.transfers, data.transfer_id, "Waste transfer")
            if t.status != TransferStatus.DELIVERED:
                raise BusinessRuleError("Only delivered transfers can be segregated")
            if t.center_id != center.id or t.waste_category_id != data.waste_category_id:
                raise BusinessRuleError("Transfer does not match the given center / waste category")
            already = self.db.scalar(
                select(func.coalesce(func.sum(WasteSegregation.incoming_quantity_kg), 0.0)).where(
                    WasteSegregation.transfer_id == t.id, WasteSegregation.is_deleted.is_(False)
                )
            ) or 0.0
            if already + data.incoming_quantity_kg > t.quantity_kg + 1e-6:
                raise BusinessRuleError(f"Segregated quantity would exceed the transfer ({t.quantity_kg} kg, {already} kg already recorded)")
        elif not self.centers.accepts(center, data.waste_category_id):
            raise BusinessRuleError(f"{center.name} does not accept this waste category")

        with transaction(self.db):
            rec = self.repo.add(WasteSegregation(recorded_by_id=actor.id, **data.model_dump()))
            self.audit.log(
                actor,
                "SEGREGATION_RECORDED",
                "waste_segregation",
                rec.id,
                {"incoming": rec.incoming_quantity_kg, "recyclable": rec.recyclable_kg, "contaminated": rec.contaminated_kg},
            )
        return rec

    def get(self, record_id: int) -> WasteSegregation:
        return get_or_404(self.repo, record_id, "Segregation record")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)
