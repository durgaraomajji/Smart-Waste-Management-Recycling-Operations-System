from datetime import datetime

from sqlalchemy import select, update

from app.models import PasswordReset, RefreshToken
from app.repositories.base_repository import BaseRepository
from app.models.base_model import utcnow


class AuthRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    def select(self):  # refresh tokens have no soft delete
        return select(RefreshToken)

    def save_refresh(self, user_id: int, jti: str, expires_at: datetime) -> RefreshToken:
        return self.add(RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at.replace(tzinfo=None)))

    def get_refresh(self, jti: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    def revoke_refresh(self, jti: str) -> None:
        self.db.execute(update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True))

    def revoke_all_for_user(self, user_id: int) -> None:
        self.db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True))

    # ---- password reset ----
    def create_reset(self, user_id: int, token_hash: str, expires_at: datetime) -> PasswordReset:
        return self.add(PasswordReset(user_id=user_id, token_hash=token_hash, expires_at=expires_at))

    def get_reset(self, token_hash: str) -> PasswordReset | None:
        return self.db.scalar(select(PasswordReset).where(PasswordReset.token_hash == token_hash))

    def invalidate_resets(self, user_id: int) -> None:
        self.db.execute(update(PasswordReset).where(PasswordReset.user_id == user_id).values(used=True))

    @staticmethod
    def is_expired(expires_at: datetime) -> bool:
        return expires_at < utcnow()
