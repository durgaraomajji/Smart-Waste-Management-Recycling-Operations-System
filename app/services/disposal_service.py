from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ForbiddenError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import DisposalStatus, NotificationType, UserRole
from app.models import DisposalRecord, User
from app.repositories.disposal_repository import DisposalRepository
from app.repositories.recycling_center_repository import RecyclingCenterRepository
from app.repositories.user_repository import UserRepository
from app.repositories.waste_category_repository import WasteCategoryRepository
from app.schemas.disposal import DisposalCreate
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.recycling_center_service import check_center_access
from app.utils.validators import get_or_404

APPROVERS = (UserRole.SUPER_ADMIN, UserRole.OPERATIONS_MANAGER)


class DisposalService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DisposalRepository(db)
        self.centers = RecyclingCenterRepository(db)
        self.categories = WasteCategoryRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    def create(self, actor: User, data: DisposalCreate) -> DisposalRecord:
        get_or_404(self.categories, data.waste_category_id, "Waste category")
        center = None
        if data.center_id:
            center = get_or_404(self.centers, data.center_id, "Recycling center")
            check_center_access(actor, center)
            if data.quantity_kg > center.current_load_kg:
                raise BusinessRuleError(f"Quantity exceeds the waste held at the center ({center.current_load_kg} kg)")
        responsible = data.responsible_user_id or actor.id
        if get_or_404(self.users, responsible, "Responsible person").role == UserRole.CUSTOMER:
            raise BusinessRuleError("A customer cannot be the responsible person for a disposal")
        payload = data.model_dump(exclude={"responsible_user_id"})
        with transaction(self.db):
            rec = self.repo.add(DisposalRecord(disposal_no=self.repo.next_number("DS"), responsible_user_id=responsible, **payload))
            self.audit.log(actor, "DISPOSAL_CREATED", "disposal_record", rec.id, {"kg": rec.quantity_kg, "method": rec.method.value})
            self.notify.notify_management(
                NotificationType.PENDING_APPROVAL,
                "Disposal awaiting approval",
                f"{rec.disposal_no}: {rec.quantity_kg} kg via {rec.method.value}",
                "disposal_record",
                rec.id,
            )
        return rec

    def get(self, disposal_id: int) -> DisposalRecord:
        return get_or_404(self.repo, disposal_id, "Disposal record")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def decide(self, actor: User, disposal_id: int, approve: bool, remarks: str | None) -> DisposalRecord:
        rec = self.get(disposal_id)
        if actor.role not in APPROVERS:
            raise ForbiddenError("Only an operations manager or super admin can approve disposals")
        if rec.status != DisposalStatus.PENDING_APPROVAL:
            raise BusinessRuleError(f"Disposal is already {rec.status.value}")
        if rec.responsible_user_id == actor.id:
            raise ForbiddenError("The person responsible for a disposal cannot approve it")
        center = self.centers.get(rec.center_id) if rec.center_id else None
        with transaction(self.db):
            rec.status = DisposalStatus.APPROVED if approve else DisposalStatus.REJECTED
            rec.approved_by_id = actor.id
            rec.approved_at = datetime.utcnow()
            if remarks:
                rec.remarks = remarks
            if approve and center:
                if rec.quantity_kg > center.current_load_kg:
                    raise BusinessRuleError("Center no longer holds enough waste for this disposal")
                center.current_load_kg = round(center.current_load_kg - rec.quantity_kg, 2)
            self.audit.log(actor, "DISPOSAL_APPROVED" if approve else "DISPOSAL_REJECTED", "disposal_record", rec.id, {"remarks": remarks})
            self.notify.notify(
                NotificationType.PENDING_APPROVAL,
                f"Disposal {rec.status.value}",
                f"{rec.disposal_no} was {rec.status.value}",
                user_id=rec.responsible_user_id,
                entity_type="disposal_record",
                entity_id=rec.id,
            )
        return rec

    def mark_disposed(self, actor: User, disposal_id: int) -> DisposalRecord:
        rec = self.get(disposal_id)
        if rec.center_id:
            check_center_access(actor, self.centers.get(rec.center_id))
        if rec.status != DisposalStatus.APPROVED:
            raise BusinessRuleError("Only approved disposals can be marked as disposed")
        with transaction(self.db):
            rec.status = DisposalStatus.DISPOSED
            self.audit.log(actor, "DISPOSAL_COMPLETED", "disposal_record", rec.id)
        return rec
