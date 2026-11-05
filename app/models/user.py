from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import AuthProvider, UserRole
from app.models.base_model import BaseModel, EnumType


class User(Base, BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # null for OAuth-only users
    role: Mapped[UserRole] = mapped_column(EnumType(UserRole), default=UserRole.CUSTOMER, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auth_provider: Mapped[AuthProvider] = mapped_column(EnumType(AuthProvider), default=AuthProvider.LOCAL, nullable=False)
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
