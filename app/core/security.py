import hashlib
import re
import secrets

from passlib.context import CryptContext

from app.constants import MIN_PASSWORD_LENGTH

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> str:
    """Raise ValueError when the password does not meet the policy."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain a digit")
    return password


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Opaque tokens (refresh / password reset) are stored hashed, never in clear text."""
    return hashlib.sha256(token.encode()).hexdigest()
