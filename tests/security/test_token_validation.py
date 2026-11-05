from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.core.jwt import create_refresh_token
from tests.factories.user_factory import admin_headers

URL = "/api/v1/auth/me"


def test_missing_token_401(client):
    assert client.get(URL).status_code == 401


def test_garbage_token_401(client):
    assert client.get(URL, headers={"Authorization": "Bearer not.a.token"}).status_code == 401


def test_wrong_signature_401(client):
    forged = jwt.encode({"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "other-secret", algorithm="HS256")
    assert client.get(URL, headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_401(client):
    expired = jwt.encode({"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert client.get(URL, headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_refresh_token_cannot_authenticate_api(client):
    refresh, _, _ = create_refresh_token(1)
    assert client.get(URL, headers={"Authorization": f"Bearer {refresh}"}).status_code == 401


def test_access_token_cannot_be_used_to_refresh(client):
    h = admin_headers(client)
    token = h["Authorization"].split()[1]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": token}).status_code == 401


def test_deleted_user_token_rejected(client, db):
    from app.models import User
    h = admin_headers(client)
    assert client.get(URL, headers=h).status_code == 200
    db.query(User).filter_by(email="admin@example.com").update({"is_deleted": True})
    db.commit()
    assert client.get(URL, headers=h).status_code == 401


def test_error_body_shape_and_request_id(client):
    r = client.get(URL)
    body = r.json()
    assert body["success"] is False and body["error"]["code"] == "unauthorized"
    assert r.headers.get("x-request-id")
