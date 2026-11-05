from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.pagination import Page, PageParams
from app.core.permissions import ADMINS, MANAGEMENT
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import get_current_user, require_roles
from app.enums import UserRole
from app.models import User
from app.schemas.user import RoleUpdate, UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=Page[UserOut])
def list_users(
    params: PageParams = Depends(),
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    _: User = Depends(require_roles(*MANAGEMENT)),
    db: Session = Depends(get_db),
):
    return UserService(db).list(params, search=search, role=role, is_active=is_active)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create a staff account (super admin)")
def create_user(data: UserCreate, actor: User = Depends(require_roles(*ADMINS)), db: Session = Depends(get_db)):
    return UserService(db).create(actor, data)


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return UserService(db).update_profile(user, data)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return UserService(db).get(user_id)


@router.patch("/{user_id}/activate", response_model=UserOut)
def activate(user_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return UserService(db).set_active(actor, user_id, True)


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate(user_id: int, actor: User = Depends(require_roles(*MANAGEMENT)), db: Session = Depends(get_db)):
    return UserService(db).set_active(actor, user_id, False)


@router.patch("/{user_id}/role", response_model=UserOut)
def change_role(user_id: int, data: RoleUpdate, actor: User = Depends(require_roles(*ADMINS)), db: Session = Depends(get_db)):
    return UserService(db).change_role(actor, user_id, data)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(user_id: int, actor: User = Depends(require_roles(*ADMINS)), db: Session = Depends(get_db)):
    UserService(db).delete(actor, user_id)
    return {"message": "User deleted"}
