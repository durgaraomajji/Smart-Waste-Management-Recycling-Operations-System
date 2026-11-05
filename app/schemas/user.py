from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength
from app.enums import AuthProvider, UserRole
from app.schemas.common import ORMModel


class UserOut(ORMModel):
    id: int
    email: str  # plain str: responses must never fail on already-stored addresses
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_email_verified: bool
    auth_provider: AuthProvider
    avatar_url: str | None = None
    last_login_at: datetime | None
    created_at: datetime


class UserCreate(BaseModel):
    """Admin-created account (any role)."""
    email: EmailStr
    password: str
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = None
    role: UserRole

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = None


class RoleUpdate(BaseModel):
    role: UserRole
