"""End-to-end API check for auth UI flows (signup OTP, reset, constraints)."""
from __future__ import annotations

import time
import uuid

import httpx

BASE = "http://127.0.0.1:8000"


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=30.0)
    assert client.get("/health").json()["status"] == "healthy"
    cfg = client.get("/auth/config").json()
    print("config:", {k: cfg[k] for k in ("smtp_configured", "dev_show_otp", "google_enabled", "smtp_provider")})

    # Email constraint: reject bad
    bad = client.post("/auth/register", json={"email": "bad", "password": "password123", "name": "X"})
    assert bad.status_code == 422, bad.text
    print("OK reject malformed email")

    # Password constraint: reject no digit
    nodigit = client.post(
        "/auth/register",
        json={"email": f"x{uuid.uuid4().hex[:6]}@yahoo.com", "password": "abcdefgh", "name": "X"},
    )
    assert nodigit.status_code == 422, nodigit.text
    print("OK reject password without digit")

    stamp = uuid.uuid4().hex[:8]
    email = f"ayesha.demo.{stamp}@gmail.com"

    # Signup + verify OTP
    reg = client.post(
        "/auth/register",
        json={"email": email, "password": "DemoPass1", "name": "Ayesha Demo"},
    )
    assert reg.status_code == 200, reg.text
    resent = client.post("/auth/resend-otp", json={"email": email, "purpose": "email_verify"})
    assert resent.status_code == 200, resent.text
    code = resent.json().get("debug_code")
    assert code, f"expected debug_code when SMTP off/dev; got {resent.json()}"
    print("OK signup OTP issued", code)

    verify = client.post(
        "/auth/verify-otp",
        json={"email": email, "code": code, "purpose": "email_verify"},
    )
    assert verify.status_code == 200, verify.text
    token = verify.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email_verified"] is True
    print("OK email verified + JWT")

    # Login
    login = client.post("/auth/login", json={"email": email, "password": "DemoPass1"})
    assert login.status_code == 200, login.text
    print("OK login")

    # Forgot / reset with Yahoo-style second account too
    edu = f"student.{stamp}@university.edu"
    client.post("/auth/register", json={"email": edu, "password": "EduPass12", "name": "Edu User"})
    forgot = client.post("/auth/forgot-password", json={"email": edu})
    assert forgot.status_code == 200, forgot.text
    rcode = forgot.json()["debug_code"]
    verified = client.post(
        "/auth/verify-otp",
        json={"email": edu, "code": rcode, "purpose": "password_reset"},
    )
    assert verified.status_code == 200, verified.text
    reset_token = verified.json()["reset_token"]
    reset = client.post(
        "/auth/reset-password",
        json={"reset_token": reset_token, "password": "NewEdu99"},
    )
    assert reset.status_code == 200, reset.text
    assert client.post("/auth/login", json={"email": edu, "password": "NewEdu99"}).status_code == 200
    print("OK edu domain forgot->reset->login")

    yahoo = f"buddy.{stamp}@yahoo.com"
    assert (
        client.post(
            "/auth/register",
            json={"email": yahoo, "password": "YahooPass1", "name": "Yahoo User"},
        ).status_code
        == 200
    )
    print("OK yahoo domain signup")

    print("AUTH API FLOW PASSED")


if __name__ == "__main__":
    # give vite a moment if started in parallel
    time.sleep(0.2)
    main()
