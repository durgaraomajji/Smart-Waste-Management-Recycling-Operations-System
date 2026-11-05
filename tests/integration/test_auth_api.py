from tests.factories.user_factory import PASSWORD, admin_headers, create_user, login
from app.enums import UserRole

BASE = "/api/v1/auth"


def test_register_login_me(client):
    r = client.post(f"{BASE}/register", json={"email": "c@example.com", "password": PASSWORD, "full_name": "Cust Omer"})
    assert r.status_code == 201 and r.json()["role"] == "customer"
    h = login(client, "c@example.com")
    me = client.get(f"{BASE}/me", headers=h)
    assert me.status_code == 200 and me.json()["email"] == "c@example.com"


def test_register_cannot_choose_role(client):
    r = client.post(f"{BASE}/register", json={"email": "x@example.com", "password": PASSWORD, "full_name": "Sneaky", "role": "super_admin"})
    assert r.status_code == 201 and r.json()["role"] == "customer"


def test_duplicate_registration_conflict(client):
    body = {"email": "d@example.com", "password": PASSWORD, "full_name": "Dup Licate"}
    assert client.post(f"{BASE}/register", json=body).status_code == 201
    assert client.post(f"{BASE}/register", json=body).status_code == 409


def test_weak_password_422(client):
    r = client.post(f"{BASE}/register", json={"email": "w@example.com", "password": "weak", "full_name": "Weak One"})
    assert r.status_code == 422


def test_wrong_password_401(client, db):
    create_user(db, UserRole.CUSTOMER, "u@example.com")
    r = client.post(f"{BASE}/login", data={"username": "u@example.com", "password": "Nope12345"})
    assert r.status_code == 401


def test_refresh_rotation_and_logout(client, db):
    create_user(db, UserRole.CUSTOMER, "r@example.com")
    tokens = client.post(f"{BASE}/login", data={"username": "r@example.com", "password": PASSWORD}).json()
    new = client.post(f"{BASE}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert new.status_code == 200
    # the old refresh token is single use
    assert client.post(f"{BASE}/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post(f"{BASE}/logout", json={"refresh_token": new.json()["refresh_token"]}).status_code == 200
    assert client.post(f"{BASE}/refresh", json={"refresh_token": new.json()["refresh_token"]}).status_code == 401


def test_password_reset_flow(client, db):
    create_user(db, UserRole.CUSTOMER, "p@example.com")
    r = client.post(f"{BASE}/forgot-password", json={"email": "p@example.com"})
    token = r.json()["reset_token"]
    assert token
    assert client.post(f"{BASE}/reset-password", json={"token": token, "new_password": "NewPassw0rd!"}).status_code == 200
    # token is single use
    assert client.post(f"{BASE}/reset-password", json={"token": token, "new_password": "Another1Pass"}).status_code == 400
    assert client.post(f"{BASE}/login", data={"username": "p@example.com", "password": "NewPassw0rd!"}).status_code == 200


def test_forgot_password_does_not_reveal_unknown_email(client):
    r = client.post(f"{BASE}/forgot-password", json={"email": "ghost@example.com"})
    assert r.status_code == 200 and r.json()["reset_token"] is None


def test_google_endpoints_report_not_configured(client):
    assert client.get(f"{BASE}/google/status").json()["detail"]
    assert client.get(f"{BASE}/google/login").status_code == 501
