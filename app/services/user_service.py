from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PageParams, paginate
from app.core.security import hash_password
from app.database.transaction import transaction
from app.enums import AuthProvider, UserRole
from app.models import User
from app.repositories.auth_repository import AuthRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import RoleUpdate, UserCreate, UserUpdate
from app.services.audit_service import AuditService


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
        self.audit = AuditService(db)

    def get(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def list(self, params: PageParams, **filters):
        return paginate(self.db, self.repo.filtered(**filters), params)

    def create(self, actor: User, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise ConflictError("An account with this email already exists")
        with transaction(self.db):
            user = self.repo.add(
                User(
                    email=data.email.lower(),
                    full_name=data.full_name.strip(),
                    phone=data.phone,
                    hashed_password=hash_password(data.password),
                    role=data.role,
                    auth_provider=AuthProvider.LOCAL,
                    is_email_verified=True,
                )
            )
            self.audit.log(actor, "USER_CREATED", "user", user.id, {"role": data.role.value})
        return user

    def update_profile(self, user: User, data: UserUpdate) -> User:
        with transaction(self.db):
            self.repo.update(user, data.model_dump(exclude_unset=True))
        return user

    def set_active(self, actor: User, user_id: int, active: bool) -> User:
        user = self.get(user_id)
        if user.id == actor.id:
            raise ForbiddenError("You cannot change the status of your own account")
        if user.role == UserRole.SUPER_ADMIN and actor.role != UserRole.SUPER_ADMIN:
            raise ForbiddenError("Only a super admin can modify another super admin")
        with transaction(self.db):
            user.is_active = active
            if not active:
                AuthRepository(self.db).revoke_all_for_user(user.id)  # kill existing sessions
            self.audit.log(actor, "USER_ACTIVATED" if active else "USER_DEACTIVATED", "user", user.id)
        return user

    def change_role(self, actor: User, user_id: int, data: RoleUpdate) -> User:
        user = self.get(user_id)
        if user.id == actor.id:
            raise ForbiddenError("You cannot change your own role")
        with transaction(self.db):
            old = user.role
            user.role = data.role
            self.audit.log(actor, "USER_ROLE_CHANGED", "user", user.id, {"from": old.value, "to": data.role.value})
        return user

    def delete(self, actor: User, user_id: int) -> None:
        user = self.get(user_id)
        if user.id == actor.id:
            raise ForbiddenError("You cannot delete your own account")
        with transaction(self.db):
            self.repo.soft_delete(user)
            user.is_active = False
            self.audit.log(actor, "USER_DELETED", "user", user.id)
