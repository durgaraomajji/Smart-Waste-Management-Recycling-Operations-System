from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength
from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        return validate_password_strength(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _pw(cls, v):
        return validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _pw(cls, v):
        return validate_password_strength(v)


class GoogleLoginResponse(BaseModel):
    authorization_url: str | None = None
    detail: str | None = None


class OAuthTokenResponse(TokenResponse):
    is_new_user: bool = False


class ForgotPasswordResponse(ORMModel):
    message: str
    # Only populated outside production so the flow can be tested without an e-mail provider
    reset_token: str | None = None
