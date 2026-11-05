import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_token(subject: str, token_type: str, expires: timedelta, extra: dict | None = None) -> tuple[str, str, datetime]:
    jti = uuid.uuid4().hex
    expire = _now() + expires
    payload = {"sub": subject, "type": token_type, "jti": jti, "iat": _now(), "exp": expire}
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti, expire


def create_access_token(user_id: int, role: str) -> str:
    token, _, _ = _create_token(
        str(user_id), "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), {"role": role}
    )
    return token


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at). The jti is persisted so the token can be revoked / rotated."""
    return _create_token(str(user_id), "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError(f"Expected a {expected_type} token")
    return payload
