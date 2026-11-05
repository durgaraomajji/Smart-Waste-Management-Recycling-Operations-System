from app.core.security import hash_password
from app.enums import UserRole
from app.models import User

PASSWORD = "Passw0rd!"


def create_user(db, role: UserRole, email: str | None = None, active: bool = True) -> User:
    user = User(
        email=email or f"{role.value}@example.com",
        full_name=role.value.replace("_", " ").title(),
        hashed_password=hash_password(PASSWORD),
        role=role,
        is_active=active,
    )
    db.add(user)
    db.commit()
    return user


def login(client, email: str, password: str = PASSWORD) -> dict:
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def headers_for(client, db, role: UserRole) -> dict:
    email = f"{role.value}@example.com"
    from app.models import User

    if not db.query(User).filter_by(email=email).first():
        create_user(db, role, email)
    return login(client, email)


def admin_headers(client) -> dict:
    return login(client, "admin@example.com", "Admin@12345")
