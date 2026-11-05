import pytest

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import hash_password, validate_password_strength, verify_password
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService


def test_password_hash_roundtrip():
    h = hash_password("Secret123")
    assert h != "Secret123" and verify_password("Secret123", h) and not verify_password("wrong", h)
    assert not verify_password("x", None)


@pytest.mark.parametrize("pw", ["short1A", "alllowercase1", "ALLUPPERCASE1", "NoDigitsHere"])
def test_weak_passwords_rejected(pw):
    with pytest.raises(ValueError):
        validate_password_strength(pw)


def test_token_types_are_not_interchangeable():
    access = create_access_token(1, "customer")
    refresh, _, _ = create_refresh_token(1)
    assert decode_token(access, "access")["sub"] == "1"
    with pytest.raises(UnauthorizedError):
        decode_token(access, "refresh")
    with pytest.raises(UnauthorizedError):
        decode_token(refresh, "access")


def test_register_creates_customer_and_blocks_duplicates(db):
    svc = AuthService(db)
    user = svc.register(RegisterRequest(email="New@Example.com", password="Passw0rd!", full_name="New User"))
    assert user.email == "new@example.com" and user.role.value == "customer"
    with pytest.raises(ConflictError):
        svc.register(RegisterRequest(email="new@example.com", password="Passw0rd!", full_name="Again"))


def test_google_login_registers_then_reuses_account(db):
    svc = AuthService(db)
    info = {"sub": "g-123", "email": "g@example.com", "email_verified": True, "name": "G User"}
    tokens, created = svc.login_or_register_google(info)
    assert created and tokens.access_token
    _, created_again = svc.login_or_register_google(info)
    assert not created_again


def test_google_login_rejects_unverified_email(db):
    from app.core.exceptions import BadRequestError

    with pytest.raises(BadRequestError):
        AuthService(db).login_or_register_google({"sub": "x", "email": "x@example.com", "email_verified": False})


def test_google_login_links_existing_local_account(db):
    svc = AuthService(db)
    svc.register(RegisterRequest(email="link@example.com", password="Passw0rd!", full_name="Link Me"))
    _, created = svc.login_or_register_google({"sub": "g-9", "email": "link@example.com", "email_verified": True})
    assert not created
