import re

from app.core.exceptions import BadRequestError, NotFoundError
from app.enums import UserRole

_PHONE_RE = re.compile(r"^\+?[0-9\- ]{7,20}$")


def get_or_404(repo, id_: int, label: str):
    obj = repo.get(id_)
    if obj is None:
        raise NotFoundError(f"{label} not found")
    return obj


def validate_phone(phone: str | None) -> str | None:
    if phone is None:
        return None
    if not _PHONE_RE.match(phone):
        raise BadRequestError("Invalid phone number format")
    return phone


def require_user_with_role(user_repo, user_id: int, roles: tuple[UserRole, ...], label: str):
    """Fetch a user and make sure they hold one of the allowed roles (e.g. supervisor assignment)."""
    user = user_repo.get(user_id)
    if user is None:
        raise NotFoundError(f"{label} not found")
    if user.role not in roles:
        allowed = ", ".join(r.value for r in roles)
        raise BadRequestError(f"{label} must have one of the roles: {allowed}")
    if not user.is_active:
        raise BadRequestError(f"{label} account is deactivated")
    return user
