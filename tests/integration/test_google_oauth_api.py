"""Google OAuth2 sign-up/login flow with a fake Google client (no network)."""
from types import SimpleNamespace

import pytest
from fastapi.responses import RedirectResponse

from app.core.config import settings

B = "/api/v1/auth"


class FakeGoogle:
    def __init__(self, userinfo=None, fail=False):
        self.userinfo_data = userinfo
        self.fail = fail

    async def authorize_redirect(self, request, redirect_uri):
        return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?redirect_uri={redirect_uri}")

    async def authorize_access_token(self, request):
        if self.fail:
            from authlib.integrations.base_client import OAuthError
            raise OAuthError(error="access_denied")
        return {"userinfo": self.userinfo_data}


@pytest.fixture
def google(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")

    def install(**kw):
        fake = FakeGoogle(**kw)
        monkeypatch.setattr("app.api.v1.endpoints.auth.oauth", SimpleNamespace(google=fake))
        return fake

    return install


INFO = {"sub": "google-1", "email": "new.user@example.com", "email_verified": True, "name": "New User", "picture": "https://img.example.com/p.jpg"}


def test_login_redirects_to_google(client, google):
    google()
    r = client.get(f"{B}/google/login", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"].startswith("https://accounts.google.com/")
    assert client.get(f"{B}/google/status").json()["authorization_url"] == "/api/v1/auth/google/login"


def test_first_google_login_registers_customer_then_signs_in(client, google):
    google(userinfo=INFO)
    first = client.get(f"{B}/google/callback").json()
    assert first["is_new_user"] is True and first["access_token"] and first["refresh_token"]
    me = client.get(f"{B}/me", headers={"Authorization": f"Bearer {first['access_token']}"}).json()
    assert me["email"] == "new.user@example.com" and me["role"] == "customer"
    assert me["auth_provider"] == "google" and me["is_email_verified"] is True
    # a customer profile exists so they can immediately request pickups
    prof = client.get("/api/v1/customers/me", headers={"Authorization": f"Bearer {first['access_token']}"})
    assert prof.status_code == 200 and prof.json()["customer_code"].startswith("CUS-")
    second = client.get(f"{B}/google/callback").json()
    assert second["is_new_user"] is False


def test_google_user_has_no_password_login(client, google):
    google(userinfo=INFO)
    client.get(f"{B}/google/callback")
    r = client.post(f"{B}/login", data={"username": "new.user@example.com", "password": "Anything1"})
    assert r.status_code == 401


def test_deactivated_google_user_blocked(client, google, db):
    from app.models import User
    google(userinfo=INFO)
    client.get(f"{B}/google/callback")
    db.query(User).filter_by(email="new.user@example.com").update({"is_active": False})
    db.commit()
    assert client.get(f"{B}/google/callback").status_code == 403


def test_oauth_error_returns_400(client, google):
    google(fail=True)
    r = client.get(f"{B}/google/callback")
    assert r.status_code == 400 and "access_denied" in r.json()["error"]["message"]


def test_unverified_google_email_rejected(client, google):
    google(userinfo={**INFO, "email_verified": False})
    assert client.get(f"{B}/google/callback").status_code == 400
