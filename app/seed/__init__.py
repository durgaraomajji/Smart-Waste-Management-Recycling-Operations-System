from sqlalchemy.orm import Session

from app.seed.seed_super_admin import seed_super_admin
from app.seed.seed_waste_categories import seed_waste_categories


def run_all(db: Session) -> None:
    print("super admin created:", seed_super_admin(db))
    print("waste categories created:", seed_waste_categories(db))

