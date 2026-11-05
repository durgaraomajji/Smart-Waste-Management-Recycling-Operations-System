from app.enums import UserRole
from tests.factories.user_factory import PASSWORD, admin_headers, create_user, login


def test_inactive_user_cannot_login(client, db):
    create_user(db, UserRole.CUSTOMER, "off@example.com", active=False)
    r = client.post("/api/v1/auth/login", data={"username": "off@example.com", "password": PASSWORD})
    assert r.status_code == 403


def test_deactivation_kills_existing_sessions(client, db):
    user = create_user(db, UserRole.CUSTOMER, "live@example.com")
    tokens = client.post("/api/v1/auth/login", data={"username": "live@example.com", "password": PASSWORD}).json()
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=h).status_code == 200
    admin = admin_headers(client)
    assert client.patch(f"/api/v1/users/{user.id}/deactivate", headers=admin).json()["is_active"] is False
    assert client.get("/api/v1/auth/me", headers=h).status_code == 403
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.patch(f"/api/v1/users/{user.id}/activate", headers=admin).json()["is_active"] is True
    assert client.post("/api/v1/auth/login", data={"username": "live@example.com", "password": PASSWORD}).status_code == 200


def test_cannot_deactivate_self_or_change_own_role(client):
    admin = admin_headers(client)
    me = client.get("/api/v1/auth/me", headers=admin).json()
    assert client.patch(f"/api/v1/users/{me['id']}/deactivate", headers=admin).status_code == 403
    assert client.patch(f"/api/v1/users/{me['id']}/role", json={"role": "customer"}, headers=admin).status_code == 403


def test_ops_manager_cannot_deactivate_super_admin(client, db):
    from tests.factories.user_factory import headers_for
    h = headers_for(client, db, UserRole.OPERATIONS_MANAGER)
    admin_id = client.get("/api/v1/auth/me", headers=admin_headers(client)).json()["id"]
    assert client.patch(f"/api/v1/users/{admin_id}/deactivate", headers=h).status_code == 403


def test_admin_creates_staff_and_soft_deletes(client):
    admin = admin_headers(client)
    r = client.post("/api/v1/users", json={"email": "ops@example.com", "password": PASSWORD, "full_name": "Ops Person", "role": "operations_manager"}, headers=admin)
    assert r.status_code == 201 and r.json()["role"] == "operations_manager"
    uid = r.json()["id"]
    assert client.delete(f"/api/v1/users/{uid}", headers=admin).status_code == 200
    assert client.get(f"/api/v1/users/{uid}", headers=admin).status_code == 404
    assert client.post("/api/v1/auth/login", data={"username": "ops@example.com", "password": PASSWORD}).status_code == 401


def test_actions_are_audited(client):
    admin = admin_headers(client)
    logs = client.get("/api/v1/audit-logs?action=USER_LOGIN", headers=admin).json()
    assert logs["total"] == 1 and logs["items"][0]["actor_email"] == "admin@example.com"
