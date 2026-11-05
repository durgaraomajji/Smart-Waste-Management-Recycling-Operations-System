from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import CenterStatus, ProcessingStatus
from app.models import ProcessingBatch, User
from app.repositories.processing_repository import ProcessingRepository
from app.repositories.recycling_center_repository import RecyclingCenterRepository
from app.repositories.waste_category_repository import WasteCategoryRepository
from app.schemas.processing_batch import BatchComplete, BatchCreate
from app.services.audit_service import AuditService
from app.services.recycling_center_service import check_center_access
from app.utils.calculation_utils import recycling_yield
from app.utils.validators import get_or_404


class ProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProcessingRepository(db)
        self.centers = RecyclingCenterRepository(db)
        self.categories = WasteCategoryRepository(db)
        self.audit = AuditService(db)

    def create(self, actor: User, data: BatchCreate) -> ProcessingBatch:
        center = get_or_404(self.centers, data.center_id, "Recycling center")
        check_center_access(actor, center)
        category = get_or_404(self.categories, data.waste_category_id, "Waste category")
        if center.status not in (CenterStatus.ACTIVE, CenterStatus.FULL):
            raise BusinessRuleError(f"Center cannot process waste (status: {center.status.value})")
        if not self.centers.accepts(center, category.id):
            raise BusinessRuleError(f"{center.name} does not process {category.name}")
        if data.input_quantity_kg > center.current_load_kg:
            raise BusinessRuleError(f"Input exceeds the waste held at the center ({center.current_load_kg} kg)")
        with transaction(self.db):
            batch = self.repo.add(
                ProcessingBatch(batch_no=self.repo.next_number("PB"), created_by_id=actor.id, **data.model_dump())
            )
            center.current_load_kg = round(center.current_load_kg - data.input_quantity_kg, 2)  # reserved for the batch
            self.audit.log(actor, "PROCESSING_BATCH_CREATED", "processing_batch", batch.id, {"input_kg": batch.input_quantity_kg})
        return batch

    def get(self, batch_id: int) -> ProcessingBatch:
        return get_or_404(self.repo, batch_id, "Processing batch")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def start(self, actor: User, batch_id: int) -> ProcessingBatch:
        batch = self.get(batch_id)
        check_center_access(actor, self.centers.get(batch.center_id))
        if batch.status != ProcessingStatus.PLANNED:
            raise BusinessRuleError(f"Only planned batches can be started (status: {batch.status.value})")
        with transaction(self.db):
            batch.status = ProcessingStatus.IN_PROGRESS
            self.audit.log(actor, "PROCESSING_STARTED", "processing_batch", batch.id)
        return batch

    def complete(self, actor: User, batch_id: int, data: BatchComplete) -> ProcessingBatch:
        batch = self.get(batch_id)
        check_center_access(actor, self.centers.get(batch.center_id))
        if batch.status != ProcessingStatus.IN_PROGRESS:
            raise BusinessRuleError(f"Only batches in progress can be completed (status: {batch.status.value})")
        if data.recycled_output_kg + data.processing_loss_kg > batch.input_quantity_kg + 1e-6:
            raise BusinessRuleError("Recycled output plus processing loss cannot exceed the input quantity")
        with transaction(self.db):
            batch.recycled_output_kg = data.recycled_output_kg
            batch.processing_loss_kg = data.processing_loss_kg
            batch.yield_percentage = recycling_yield(data.recycled_output_kg, batch.input_quantity_kg)
            batch.status = ProcessingStatus.COMPLETED
            self.audit.log(
                actor,
                "PROCESSING_COMPLETED",
                "processing_batch",
                batch.id,
                {"output_kg": data.recycled_output_kg, "loss_kg": data.processing_loss_kg, "yield_pct": batch.yield_percentage},
            )
        return batch

    def fail(self, actor: User, batch_id: int) -> ProcessingBatch:
        batch = self.get(batch_id)
        center = self.centers.get(batch.center_id)
        check_center_access(actor, center)
        if batch.status not in (ProcessingStatus.PLANNED, ProcessingStatus.IN_PROGRESS):
            raise BusinessRuleError(f"Batch in status '{batch.status.value}' cannot be failed")
        with transaction(self.db):
            batch.status = ProcessingStatus.FAILED
            center.current_load_kg = round(center.current_load_kg + batch.input_quantity_kg, 2)  # waste returns to stock
            self.audit.log(actor, "PROCESSING_FAILED", "processing_batch", batch.id)
        return batch
