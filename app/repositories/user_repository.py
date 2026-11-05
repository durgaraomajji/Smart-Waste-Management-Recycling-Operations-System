from sqlalchemy import or_

from app.enums import UserRole
from app.models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.get_by(email=email.lower())

    def get_by_google_sub(self, sub: str) -> User | None:
        return self.get_by(google_sub=sub)

    def filtered(self, search: str | None = None, role: UserRole | None = None, is_active: bool | None = None):
        stmt = self.select()
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
        if role:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active.is_(is_active))
        return stmt.order_by(User.id.desc())
