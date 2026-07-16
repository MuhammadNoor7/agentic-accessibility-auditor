"""Live backend auth E2E: signup, OTP, resend, login, forgot, reset, SMTP, Google config."""
from __future__ import annotations

import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

BASE = "http://127.0.0.1:8001"


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=60.0)
    stamp = uuid.uuid4().hex[:8]
    email = f"axion.e2e.{stamp}@gmail.com"
    password = "TestPass12"
    new_password = "NewPass99"
    results: dict[str, str] = {}

    print("1) health")
    assert client.get("/health").json()["status"] == "healthy"
    results["health"] = "PASS"

    print("2) auth config")
    cfg = client.get("/auth/config").json()
    print(
        "   ",
        {
            k: cfg.get(k)
            for k in (
                "google_enabled",
                "google_client_id",
                "smtp_configured",
                "smtp_from",
                "dev_show_otp",
                "smtp_provider",
            )
        },
    )
    assert cfg["google_enabled"] is True, cfg
    assert cfg["google_client_id"] and "apps.googleusercontent.com" in cfg["google_client_id"]
    assert cfg["smtp_configured"] is True, cfg
    assert cfg["dev_show_otp"] is True, "need AUTH_DEV_SHOW_OTP=1 for automated OTP verify"
    results["google_config"] = "PASS"
    results["smtp_configured_flag"] = "PASS"

    print("3) reject bad email / weak password")
    assert client.post(
        "/auth/register", json={"email": "bad", "password": password, "name": "X"}
    ).status_code == 422
    assert client.post(
        "/auth/register",
        json={"email": f"weak.{stamp}@yahoo.com", "password": "abcdefgh", "name": "X"},
    ).status_code == 422
    results["validation"] = "PASS"

    print("4) signup")
    reg = client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": "E2E User"},
    )
    assert reg.status_code == 200, reg.text
    results["signup"] = "PASS"

    print("5) resend OTP (+ SMTP attempt)")
    resent = client.post(
        "/auth/resend-otp",
        json={"email": email, "purpose": "email_verify"},
    )
    assert resent.status_code == 200, resent.text
    body = resent.json()
    code = body.get("debug_code")
    assert code and len(code) == 6, body
    if "email delivery failed" in (body.get("message") or "").lower() or "535" in (
        body.get("message") or ""
    ):
        results["smtp_send"] = "FAIL (Gmail 535 BadCredentials — regenerate App Password)"
        print("   SMTP send FAILED — continuing with debug_code")
        print("  ", body.get("message", "")[:180])
    else:
        results["smtp_send"] = "PASS (no failure message)"
    print(f"   OTP debug_code={code}")
    results["resend_otp"] = "PASS"

    print("6) verify OTP -> JWT")
    verified = client.post(
        "/auth/verify-otp",
        json={"email": email, "code": code, "purpose": "email_verify"},
    )
    assert verified.status_code == 200, verified.text
    token = verified.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email_verified"] is True
    assert me.json()["email"] == email
    results["verify_otp"] = "PASS"

    print("7) login")
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    results["login"] = "PASS"

    print("8) wrong password rejected")
    assert (
        client.post(
            "/auth/login", json={"email": email, "password": "WrongPass1"}
        ).status_code
        == 401
    )
    results["login_reject"] = "PASS"

    print("9) forgot password")
    forgot = client.post("/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200, forgot.text
    reset_code = forgot.json().get("debug_code")
    assert reset_code and len(reset_code) == 6, forgot.json()
    print(f"   reset OTP={reset_code}")
    results["forgot_password"] = "PASS"

    print("10) verify reset OTP")
    vreset = client.post(
        "/auth/verify-otp",
        json={"email": email, "code": reset_code, "purpose": "password_reset"},
    )
    assert vreset.status_code == 200, vreset.text
    reset_token = vreset.json()["reset_token"]
    results["verify_reset_otp"] = "PASS"

    print("11) reset password")
    reset = client.post(
        "/auth/reset-password",
        json={"reset_token": reset_token, "password": new_password},
    )
    assert reset.status_code == 200, reset.text
    results["reset_password"] = "PASS"

    print("12) old password fails, new password works")
    assert (
        client.post("/auth/login", json={"email": email, "password": password}).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", json={"email": email, "password": new_password}
        ).status_code
        == 200
    )
    results["login_after_reset"] = "PASS"

    print("13) yahoo/edu domain signup")
    for domain_email in (f"u.{stamp}@yahoo.com", f"s.{stamp}@university.edu"):
        r = client.post(
            "/auth/register",
            json={"email": domain_email, "password": "DomainPass1", "name": "Domain"},
        )
        assert r.status_code == 200, (domain_email, r.text)
    results["multi_domain"] = "PASS"

    print("14) google endpoint rejects garbage token (endpoint configured)")
    g = client.post("/auth/google", json={"id_token": "not.a.real.token"})
    assert g.status_code == 401, g.text
    results["google_token_verify"] = "PASS (rejects invalid token)"

    print("\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: {v}")
    failed = [k for k, v in results.items() if v.startswith("FAIL")]
    if failed:
        print("\nAUTH FLOWS PASSED; SMTP needs a new Gmail App Password.")
    else:
        print("\nALL LIVE AUTH + SMTP CHECKS PASSED")


if __name__ == "__main__":
    main()
