from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import MANAGEMENT
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import RecyclabilityStatus
from app.models import User
from app.schemas.waste_category import CategoryCreate, CategoryOut, CategoryUpdate, RuleCreate, RuleOut
from app.services.waste_category_service import WasteCategoryService

router = APIRouter(prefix="/waste-categories", tags=["Waste Categories"])


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return WasteCategoryService(db).create(actor, data)


@router.get("", response_model=Page[CategoryOut])
def list_categories(
    params: PageParams = Depends(),
    search: str | None = None,
    recyclability: RecyclabilityStatus | None = None,
    is_active: bool | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return WasteCategoryService(db).list(params, search=search, recyclability=recyclability, is_active=is_active)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return WasteCategoryService(db).get(category_id)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, data: CategoryUpdate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return WasteCategoryService(db).update(actor, category_id, data)


@router.post("/{category_id}/segregation-rules", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def add_rule(category_id: int, data: RuleCreate, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return WasteCategoryService(db).add_rule(actor, category_id, data)


@router.delete("/{category_id}/segregation-rules/{rule_id}", response_model=MessageResponse)
def delete_rule(category_id: int, rule_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    WasteCategoryService(db).delete_rule(actor, category_id, rule_id)
    return {"message": "Rule deleted"}
