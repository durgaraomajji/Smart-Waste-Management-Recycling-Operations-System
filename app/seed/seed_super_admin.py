from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.enums import AuthProvider, UserRole
from app.models import User


def seed_super_admin(db: Session) -> bool:
    if db.query(User).filter_by(email=settings.SUPER_ADMIN_EMAIL.lower()).first():
        return False
    db.add(
        User(
            email=settings.SUPER_ADMIN_EMAIL.lower(),
            full_name=settings.SUPER_ADMIN_NAME,
            hashed_password=hash_password(settings.SUPER_ADMIN_PASSWORD),
            role=UserRole.SUPER_ADMIN,
            auth_provider=AuthProvider.LOCAL,
            is_email_verified=True,
        )
    )
    db.commit()
    return True
