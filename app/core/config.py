from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Smart Waste Management & Recycling Operations System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database - MySQL / PostgreSQL in production, SQLite fallback for quick local runs
    DATABASE_URL: str = "sqlite:///./waste.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Session secret (only used by the OAuth2 redirect handshake)
    SESSION_SECRET: str = "change-me-session-secret"

    # Google OAuth2 sign-up / login
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Seed super admin
    SUPER_ADMIN_EMAIL: str = "admin@example.com"
    SUPER_ADMIN_PASSWORD: str = "Admin@12345"
    SUPER_ADMIN_NAME: str = "Super Admin"

    # Optional Redis
    REDIS_URL: str | None = None

    # comma-separated in .env; NoDecode stops pydantic-settings from expecting JSON
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def google_enabled(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
