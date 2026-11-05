from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.constants import API_V1_PREFIX
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.jwt import decode_token
from app.database.session import get_db
from app.enums import UserRole
from app.models import User
from app.repositories.user_repository import UserRepository

# Swagger's "Authorize" button posts to this URL using the OAuth2 password flow (username = e-mail)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token, "access")
    user = UserRepository(db).get(int(payload["sub"]))
    if user is None:
        raise UnauthorizedError("User no longer exists")
    if not user.is_active:
        raise ForbiddenError("Account is deactivated")
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory for role-based access control. Super admin always passes."""
    allowed = set(roles) | {UserRole.SUPER_ADMIN}

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise ForbiddenError("You do not have permission to perform this action")
        return user

    return checker


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
