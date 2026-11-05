from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import generate_token, hash_password, hash_token, verify_password
from app.constants import PASSWORD_RESET_EXPIRE_MINUTES
from app.database.transaction import transaction
from app.enums import AuthProvider, UserRole
from app.models import Customer, User
from app.models.base_model import utcnow
from app.repositories.auth_repository import AuthRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.tokens = AuthRepository(db)
        self.customers = CustomerRepository(db)
        self.audit = AuditService(db)

    # ------------------------------------------------------------ registration
    def _create_customer_profile(self, user: User) -> Customer:
        return self.customers.add(
            Customer(
                user_id=user.id,
                customer_code=self.customers.next_number("CUS"),
                full_name=user.full_name,
                email=user.email,
                phone=user.phone,
            )
        )

    def register(self, data: RegisterRequest, ip: str | None = None) -> User:
        """Public sign-up. Always creates a CUSTOMER account; staff accounts are created by admins."""
        email = data.email.lower()
        if self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists")
        with transaction(self.db):
            user = self.users.add(
                User(
                    email=email,
                    full_name=data.full_name.strip(),
                    phone=data.phone,
                    hashed_password=hash_password(data.password),
                    role=UserRole.CUSTOMER,
                    auth_provider=AuthProvider.LOCAL,
                )
            )
            self._create_customer_profile(user)
            self.audit.log(user, "USER_REGISTERED", "user", user.id, {"provider": "local"}, ip)
        return user

    # ------------------------------------------------------------------ tokens
    def issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token(user.id, user.role.value)
        refresh, jti, expires = create_refresh_token(user.id)
        self.tokens.save_refresh(user.id, jti, expires)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # --------------------------------------------------------------------- login
    def login(self, email: str, password: str, ip: str | None = None) -> TokenResponse:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        if not user.is_active:
            raise ForbiddenError("Account is deactivated")
        with transaction(self.db):
            user.last_login_at = utcnow()
            tokens = self.issue_tokens(user)
            self.audit.log(user, "USER_LOGIN", "user", user.id, {"provider": "local"}, ip)
        return tokens

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, "refresh")
        stored = self.tokens.get_refresh(payload["jti"])
        if not stored or stored.revoked or stored.expires_at < utcnow():
            raise UnauthorizedError("Refresh token is revoked or expired")
        user = self.users.get(int(payload["sub"]))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        with transaction(self.db):
            self.tokens.revoke_refresh(payload["jti"])  # rotation: each refresh token is single use
            tokens = self.issue_tokens(user)
        return tokens

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, "refresh")
        with transaction(self.db):
            self.tokens.revoke_refresh(payload["jti"])

    # ----------------------------------------------------------- password reset
    def forgot_password(self, email: str) -> str | None:
        """Returns the raw reset token (to be e-mailed). Callers must not reveal whether the e-mail exists."""
        user = self.users.get_by_email(email)
        if not user or not user.is_active:
            return None
        raw = generate_token()
        with transaction(self.db):
            self.tokens.invalidate_resets(user.id)
            self.tokens.create_reset(user.id, hash_token(raw), utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES))
            self.audit.log(user, "PASSWORD_RESET_REQUESTED", "user", user.id)
        return raw

    def reset_password(self, token: str, new_password: str) -> None:
        reset = self.tokens.get_reset(hash_token(token))
        if not reset or reset.used or reset.expires_at < utcnow():
            raise BadRequestError("Reset token is invalid or has expired")
        user = self.users.get(reset.user_id)
        if not user:
            raise BadRequestError("Reset token is invalid or has expired")
        with transaction(self.db):
            user.hashed_password = hash_password(new_password)
            reset.used = True
            self.tokens.revoke_all_for_user(user.id)  # sign out everywhere
            self.audit.log(user, "PASSWORD_RESET_COMPLETED", "user", user.id)

    def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.hashed_password):
            raise BadRequestError("Current password is incorrect")
        with transaction(self.db):
            user.hashed_password = hash_password(new)
            self.tokens.revoke_all_for_user(user.id)
            self.audit.log(user, "PASSWORD_CHANGED", "user", user.id)

    # -------------------------------------------------------------- Google OAuth2
    def login_or_register_google(self, userinfo: dict, ip: str | None = None) -> tuple[TokenResponse, bool]:
        """Sign in with Google, creating a CUSTOMER account on first use (OAuth2 registration).

        Matching order: google_sub -> verified e-mail (links to an existing local account) -> create new.
        """
        sub = userinfo.get("sub")
        email = (userinfo.get("email") or "").lower()
        if not sub or not email:
            raise BadRequestError("Google did not return the required profile information")
        if not userinfo.get("email_verified", False):
            raise BadRequestError("Google account e-mail is not verified")

        created = False
        with transaction(self.db):
            user = self.users.get_by_google_sub(sub)
            if user is None:
                user = self.users.get_by_email(email)
                if user is not None:
                    user.google_sub = sub  # link existing account
                    user.is_email_verified = True
                    user.avatar_url = user.avatar_url or userinfo.get("picture")
                    self.audit.log(user, "OAUTH_ACCOUNT_LINKED", "user", user.id, {"provider": "google"}, ip)
                else:
                    user = self.users.add(
                        User(
                            email=email,
                            full_name=(userinfo.get("name") or email.split("@")[0]).strip(),
                            hashed_password=None,
                            role=UserRole.CUSTOMER,
                            auth_provider=AuthProvider.GOOGLE,
                            google_sub=sub,
                            is_email_verified=True,
                            avatar_url=userinfo.get("picture"),
                        )
                    )
                    self._create_customer_profile(user)
                    self.audit.log(user, "USER_REGISTERED", "user", user.id, {"provider": "google"}, ip)
                    created = True
            if not user.is_active:
                raise ForbiddenError("Account is deactivated")
            user.last_login_at = utcnow()
            tokens = self.issue_tokens(user)
            self.audit.log(user, "USER_LOGIN", "user", user.id, {"provider": "google"}, ip)
        return tokens, created
