from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.core.oauth import oauth
from app.core.responses import MessageResponse
from app.database.session import get_db
from app.dependencies import client_ip, get_current_user
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleLoginResponse,
    LogoutRequest,
    OAuthTokenResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Register a customer account")
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).register(data, client_ip(request))


@router.post("/login", response_model=TokenResponse, summary="OAuth2 password login (form: username = e-mail)")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return AuthService(db).login(form.username, form.password, client_ip(request))


@router.post("/login/json", response_model=TokenResponse, summary="Login with a JSON body")
def login_json(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return AuthService(db).login(data.email, data.password, client_ip(request))


@router.post("/refresh", response_model=TokenResponse, summary="Exchange a refresh token for a new token pair")
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    AuthService(db).logout(data.refresh_token)
    return {"message": "Logged out"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    token = AuthService(db).forgot_password(data.email)
    # Same response whether or not the account exists (prevents e-mail enumeration).
    # The raw token is only echoed outside production so the flow can be tested without a mail server.
    expose = settings.ENVIRONMENT != "production" and token is not None
    return {"message": "If the account exists, a reset link has been sent", "reset_token": token if expose else None}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(data.token, data.new_password)
    return {"message": "Password has been reset"}


@router.post("/change-password", response_model=MessageResponse)
def change_password(data: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).change_password(user, data.current_password, data.new_password)
    return {"message": "Password changed. Please sign in again."}


@router.get("/me", response_model=UserOut, summary="Current user")
def me(user: User = Depends(get_current_user)):
    return user


# ------------------------------------------------------------------ Google OAuth2
def _require_google():
    if not settings.google_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth2 is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )


@router.get("/google/login", summary="Start Google OAuth2 sign-in / sign-up (browser redirect)")
async def google_login(request: Request):
    _require_google()
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback", response_model=OAuthTokenResponse, summary="Google OAuth2 callback - registers the user on first login")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    _require_google()
    from authlib.integrations.base_client import OAuthError

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise BadRequestError(f"Google sign-in failed: {exc.error}") from exc
    userinfo = token.get("userinfo") or await oauth.google.userinfo(token=token)
    tokens, created = await run_in_threadpool(AuthService(db).login_or_register_google, dict(userinfo), client_ip(request))
    return OAuthTokenResponse(**tokens.model_dump(), is_new_user=created)


@router.get("/google/status", response_model=GoogleLoginResponse, summary="Is Google sign-in configured?")
def google_status():
    if settings.google_enabled:
        return {"authorization_url": "/api/v1/auth/google/login"}
    return {"detail": "Google OAuth2 is not configured"}
