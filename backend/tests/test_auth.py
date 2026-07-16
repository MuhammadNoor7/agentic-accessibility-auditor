"""Tests for JWT auth (backend/auth.py, backend/routers/auth_router.py) and
per-user records persistence (backend/routers/records_router.py)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import backend.auth as auth_module
import backend.otp_store as otp_module
import backend.routers.auth_router as auth_router_module
import backend.routers.records_router as records_module
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Redirect the flat-JSON user/record/otp stores to a scratch dir per test."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr(auth_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(auth_module, "USERS_DB_PATH", data_dir / "users.db.json")
    monkeypatch.setattr(records_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(records_module, "RECORDS_DB_PATH", data_dir / "records.db.json")
    monkeypatch.setattr(otp_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(otp_module, "OTP_DB_PATH", data_dir / "otp.db.json")
    monkeypatch.setenv("AUTH_DEV_SHOW_OTP", "1")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)
    yield


def _register(
    email: str = "user@example.com",
    password: str = "password123",
    name: str = "Jane Doe",
):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name},
    )


def _record_payload(screen_id: str = "screen_1") -> dict:
    return {
        "screen_id": screen_id,
        "total_violations": 3,
        "violations_by_severity": {"High": 1, "Medium": 1, "Low": 1},
        "components_path": "outputs/components/screen_1_components.json",
        "violations_path": "outputs/violations/screen_1_violations.json",
    }


# --- register --------------------------------------------------------------


def test_register_success():
    response = _register()
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["email"] == "user@example.com"
    assert body["name"] == "Jane Doe"


def test_login_returns_persisted_name():
    _register(name="Muhammad Noor")
    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Muhammad Noor"


def test_register_duplicate_email_conflict():
    _register()
    response = _register()
    assert response.status_code == 409


def test_register_short_password_unprocessable():
    response = _register(password="short")
    assert response.status_code == 422


# --- login -------------------------------------------------------------------


def test_login_success():
    _register()
    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_unauthorized():
    _register()
    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_unknown_email_not_found():
    response = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "password123"}
    )
    assert response.status_code == 404


# --- protected route ---------------------------------------------------------


def test_me_with_valid_token():
    token = _register().json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@example.com"
    assert "hashed_password" not in body


def test_me_without_token_unauthorized():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_unauthorized():
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


# --- email verification OTP --------------------------------------------------


def test_signup_email_verify_otp_flow():
    _register(email="verify@example.com")
    resent = client.post(
        "/auth/resend-otp",
        json={"email": "verify@example.com", "purpose": "email_verify"},
    )
    assert resent.status_code == 200
    code = resent.json()["debug_code"]
    assert code and len(code) == 6

    verified = client.post(
        "/auth/verify-otp",
        json={"email": "verify@example.com", "code": code, "purpose": "email_verify"},
    )
    assert verified.status_code == 200
    body = verified.json()
    assert body["access_token"]
    assert body["email"] == "verify@example.com"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email_verified"] is True


def test_verify_otp_rejects_bad_code():
    _register(email="badcode@example.com")
    response = client.post(
        "/auth/verify-otp",
        json={"email": "badcode@example.com", "code": "000000", "purpose": "email_verify"},
    )
    assert response.status_code == 401


# --- password reset OTP ------------------------------------------------------


def test_forgot_password_reset_flow():
    _register(email="reset@example.com", password="password123")
    forgot = client.post("/auth/forgot-password", json={"email": "reset@example.com"})
    assert forgot.status_code == 200
    code = forgot.json()["debug_code"]
    assert code

    verified = client.post(
        "/auth/verify-otp",
        json={"email": "reset@example.com", "code": code, "purpose": "password_reset"},
    )
    assert verified.status_code == 200
    reset_token = verified.json()["reset_token"]
    assert reset_token

    reset = client.post(
        "/auth/reset-password",
        json={"reset_token": reset_token, "password": "newpassword99"},
    )
    assert reset.status_code == 200

    old_login = client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "password123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "newpassword99"},
    )
    assert new_login.status_code == 200
    assert new_login.json()["access_token"]


def test_forgot_password_unknown_email_no_enumeration():
    response = client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
    assert response.status_code == 200
    body = response.json()
    assert "code was sent" in body["message"].lower() or "account exists" in body["message"].lower()
    assert body.get("debug_code") in (None, "")


# --- Google Sign-In ----------------------------------------------------------


def test_google_auth_when_not_configured():
    monkey_id = auth_module.GOOGLE_CLIENT_ID
    auth_router_module.GOOGLE_CLIENT_ID = ""
    auth_module.GOOGLE_CLIENT_ID = ""
    try:
        response = client.post("/auth/google", json={"id_token": "fake.token"})
        assert response.status_code == 503
    finally:
        auth_router_module.GOOGLE_CLIENT_ID = monkey_id
        auth_module.GOOGLE_CLIENT_ID = monkey_id


def test_google_auth_with_mocked_token(monkeypatch):
    monkeypatch.setattr(auth_module, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_router_module, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    def fake_verify(id_token: str) -> dict:
        assert id_token == "valid-google-token"
        return {
            "email": "google.user@example.com",
            "email_verified": True,
            "name": "Google User",
        }

    monkeypatch.setattr(auth_router_module, "_verify_google_id_token", fake_verify)

    response = client.post("/auth/google", json={"id_token": "valid-google-token"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "google.user@example.com"
    assert body["name"] == "Google User"
    assert body["access_token"]

    # Google-only accounts cannot password-login until they set a password.
    login = client.post(
        "/auth/login",
        json={"email": "google.user@example.com", "password": "password123"},
    )
    assert login.status_code == 401


def test_auth_config_reports_google_flag(monkeypatch):
    monkeypatch.setattr(auth_module, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(auth_router_module, "GOOGLE_CLIENT_ID", "")
    off = client.get("/auth/config")
    assert off.status_code == 200
    assert off.json()["google_enabled"] is False

    monkeypatch.setattr(auth_module, "GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    monkeypatch.setattr(auth_router_module, "GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    on = client.get("/auth/config")
    assert on.status_code == 200
    assert on.json()["google_enabled"] is True
    assert on.json()["google_client_id"] == "abc.apps.googleusercontent.com"


# --- records -------------------------------------------------------------------


def test_create_record_with_valid_token():
    token = _register().json()["access_token"]
    response = client.post(
        "/records", json=_record_payload(), headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["screen_id"] == "screen_1"


def test_list_records_returns_only_current_user():
    token_a = _register(email="a@example.com").json()["access_token"]
    token_b = _register(email="b@example.com").json()["access_token"]

    client.post(
        "/records", json=_record_payload("a_screen"), headers={"Authorization": f"Bearer {token_a}"}
    )
    client.post(
        "/records", json=_record_payload("b_screen"), headers={"Authorization": f"Bearer {token_b}"}
    )

    response = client.get("/records", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["records"][0]["screen_id"] == "a_screen"


def test_delete_record_belonging_to_other_user_forbidden():
    token_a = _register(email="a@example.com").json()["access_token"]
    token_b = _register(email="b@example.com").json()["access_token"]

    created = client.post(
        "/records", json=_record_payload(), headers={"Authorization": f"Bearer {token_a}"}
    ).json()

    response = client.delete(
        f"/records/{created['record_id']}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403
