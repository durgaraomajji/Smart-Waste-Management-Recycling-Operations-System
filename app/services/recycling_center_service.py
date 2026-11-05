from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import CENTER_CAPACITY_ALERT_THRESHOLD
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.enums import CenterStatus, NotificationType, UserRole
from app.models import RecyclingCenter, User
from app.repositories.location_repository import ZoneRepository
from app.repositories.recycling_center_repository import RecyclingCenterRepository
from app.repositories.user_repository import UserRepository
from app.repositories.waste_category_repository import WasteCategoryRepository
from app.schemas.recycling_center import CenterCreate, CenterUpdate
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.calculation_utils import center_utilization
from app.utils.validators import get_or_404, require_user_with_role

MANAGER_ROLES = (UserRole.RECYCLING_CENTER_MANAGER, UserRole.OPERATIONS_MANAGER, UserRole.SUPER_ADMIN)


def check_center_access(actor: User, center: RecyclingCenter) -> None:
    """Centre managers may only operate on the centre they manage."""
    if actor.role == UserRole.RECYCLING_CENTER_MANAGER and center.manager_id != actor.id:
        raise ForbiddenError("You are not the manager of this recycling center")


class RecyclingCenterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecyclingCenterRepository(db)
        self.categories = WasteCategoryRepository(db)
        self.users = UserRepository(db)
        self.zones = ZoneRepository(db)
        self.audit = AuditService(db)
        self.notify = NotificationService(db)

    def _validate_categories(self, ids: list[int]) -> None:
        for cid in set(ids):
            get_or_404(self.categories, cid, f"Waste category {cid}")

    def create(self, actor: User, data: CenterCreate) -> RecyclingCenter:
        if self.repo.exists(name=data.name) or self.repo.exists(code=data.code.upper()):
            raise ConflictError("A recycling center with this name or code already exists")
        if data.manager_id:
            require_user_with_role(self.users, data.manager_id, MANAGER_ROLES, "Manager")
        if data.zone_id:
            get_or_404(self.zones, data.zone_id, "Zone")
        self._validate_categories(data.accepted_category_ids)
        values = data.model_dump(exclude={"accepted_category_ids"})
        values["code"] = data.code.upper()
        with transaction(self.db):
            center = self.repo.add(RecyclingCenter(**values))
            self.repo.set_categories(center, data.accepted_category_ids)
            self.audit.log(actor, "CENTER_REGISTERED", "recycling_center", center.id)
        return center

    def get(self, center_id: int, actor: User | None = None) -> RecyclingCenter:
        center = get_or_404(self.repo, center_id, "Recycling center")
        return center

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def update(self, actor: User, center_id: int, data: CenterUpdate) -> RecyclingCenter:
        center = self.get(center_id)
        values = data.model_dump(exclude_unset=True)
        if "daily_capacity_kg" in values and values["daily_capacity_kg"] < center.current_load_kg:
            raise BusinessRuleError("New capacity is below the center's current load")
        with transaction(self.db):
            self.repo.update(center, values)
            self.audit.log(actor, "CENTER_UPDATED", "recycling_center", center.id, values)
        return center

    def set_status(self, actor: User, center_id: int, status: CenterStatus) -> RecyclingCenter:
        center = self.get(center_id)
        with transaction(self.db):
            old = center.status
            center.status = status
            self.audit.log(actor, "CENTER_STATUS_CHANGED", "recycling_center", center.id, {"from": old.value, "to": status.value})
        return center

    def assign_manager(self, actor: User, center_id: int, manager_id: int) -> RecyclingCenter:
        center = self.get(center_id)
        require_user_with_role(self.users, manager_id, MANAGER_ROLES, "Manager")
        with transaction(self.db):
            center.manager_id = manager_id
            self.audit.log(actor, "CENTER_MANAGER_ASSIGNED", "recycling_center", center.id, {"manager_id": manager_id})
        return center

    def set_accepted_categories(self, actor: User, center_id: int, category_ids: list[int]) -> RecyclingCenter:
        center = self.get(center_id)
        self._validate_categories(category_ids)
        with transaction(self.db):
            self.repo.set_categories(center, category_ids)
            self.audit.log(actor, "CENTER_CATEGORIES_CHANGED", "recycling_center", center.id, {"category_ids": sorted(set(category_ids))})
        return center

    def availability(self, center_id: int) -> dict:
        c = self.get(center_id)
        return {
            "center_id": c.id,
            "status": c.status,
            "daily_capacity_kg": c.daily_capacity_kg,
            "current_load_kg": c.current_load_kg,
            "available_capacity_kg": round(max(c.daily_capacity_kg - c.current_load_kg, 0), 2),
            "utilization_pct": center_utilization(c.current_load_kg, c.daily_capacity_kg),
        }

    def delete(self, actor: User, center_id: int) -> None:
        center = self.get(center_id)
        if center.current_load_kg > 0:
            raise BusinessRuleError("Center still holds waste and cannot be deleted")
        with transaction(self.db):
            self.repo.soft_delete(center)
            self.audit.log(actor, "CENTER_DELETED", "recycling_center", center.id)

    # --------------------------------------------------------- shared helpers
    def raise_capacity_alert_if_needed(self, center: RecyclingCenter) -> None:
        """Adds a notification (inside caller's transaction) when the center nears capacity; also flips status to FULL."""
        used = center.current_load_kg / center.daily_capacity_kg if center.daily_capacity_kg else 0
        if used >= 1 and center.status == CenterStatus.ACTIVE:
            center.status = CenterStatus.FULL
        if used >= CENTER_CAPACITY_ALERT_THRESHOLD:
            msg = f"{center.name} is at {used * 100:.0f}% of daily capacity"
            self.notify.notify_management(NotificationType.CENTER_CAPACITY_ALERT, "Center capacity alert", msg, "recycling_center", center.id)
            if center.manager_id:
                self.notify.notify(
                    NotificationType.CENTER_CAPACITY_ALERT,
                    "Center capacity alert",
                    msg,
                    user_id=center.manager_id,
                    entity_type="recycling_center",
                    entity_id=center.id,
                )
