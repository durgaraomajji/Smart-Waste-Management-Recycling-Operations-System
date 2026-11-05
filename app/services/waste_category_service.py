from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.pagination import PageParams, paginate
from app.database.transaction import transaction
from app.models import SegregationRule, User, WasteCategory
from app.repositories.waste_category_repository import SegregationRuleRepository, WasteCategoryRepository
from app.schemas.waste_category import CategoryCreate, CategoryUpdate, RuleCreate
from app.services.audit_service import AuditService
from app.utils.validators import get_or_404


class WasteCategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WasteCategoryRepository(db)
        self.rules = SegregationRuleRepository(db)
        self.audit = AuditService(db)

    def create(self, actor: User, data: CategoryCreate) -> WasteCategory:
        if self.repo.exists(name=data.name) or self.repo.exists(code=data.code.upper()):
            raise ConflictError("A waste category with this name or code already exists")
        with transaction(self.db):
            cat = self.repo.add(WasteCategory(**{**data.model_dump(), "code": data.code.upper()}))
            self.audit.log(actor, "WASTE_CATEGORY_CREATED", "waste_category", cat.id)
        return cat

    def get(self, category_id: int) -> WasteCategory:
        return get_or_404(self.repo, category_id, "Waste category")

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def update(self, actor: User, category_id: int, data: CategoryUpdate) -> WasteCategory:
        cat = self.get(category_id)
        values = data.model_dump(exclude_unset=True)
        with transaction(self.db):
            self.repo.update(cat, values)
            self.audit.log(actor, "WASTE_CATEGORY_UPDATED", "waste_category", cat.id, values)
        return cat

    def add_rule(self, actor: User, category_id: int, data: RuleCreate) -> SegregationRule:
        self.get(category_id)
        with transaction(self.db):
            rule = self.rules.add(SegregationRule(waste_category_id=category_id, **data.model_dump()))
            self.audit.log(actor, "SEGREGATION_RULE_ADDED", "waste_category", category_id, {"rule_id": rule.id})
        return rule

    def delete_rule(self, actor: User, category_id: int, rule_id: int) -> None:
        rule = get_or_404(self.rules, rule_id, "Segregation rule")
        if rule.waste_category_id != category_id:
            raise ConflictError("Rule does not belong to this category")
        with transaction(self.db):
            self.rules.soft_delete(rule)
            self.audit.log(actor, "SEGREGATION_RULE_DELETED", "waste_category", category_id, {"rule_id": rule_id})
