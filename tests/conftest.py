import os

# must be set before the app is imported
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

import pytest
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import SessionLocal, engine
import app.models  # noqa: F401
from app.main import app
from app.seed import seed_super_admin, seed_waste_categories  # noqa: F401
from app.seed.seed_super_admin import seed_super_admin as _seed_admin
from app.seed.seed_waste_categories import seed_waste_categories as _seed_cats


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        _seed_admin(db)
        _seed_cats(db)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session
