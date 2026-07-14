"""Tests for JWT auth (backend/auth.py, backend/routers/auth_router.py) and
per-user records persistence (backend/routers/records_router.py)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import backend.auth as auth_module
import backend.routers.records_router as records_module
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Redirect the flat-JSON user/record stores to a scratch dir per test."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr(auth_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(auth_module, "USERS_DB_PATH", data_dir / "users.db.json")
    monkeypatch.setattr(records_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(records_module, "RECORDS_DB_PATH", data_dir / "records.db.json")
    yield


def _register(email: str = "user@example.com", password: str = "password123"):
    return client.post("/auth/register", json={"email": email, "password": password})


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
