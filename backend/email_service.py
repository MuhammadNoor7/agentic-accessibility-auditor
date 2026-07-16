"""Outbound email helper for OTP codes — Gmail SMTP (App Password) by default."""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)

# Sensible defaults for internship demos: Gmail SMTP + STARTTLS on 587.
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def smtp_user() -> str:
    return _env("SMTP_USER") or _env("SMTP_FROM")


def smtp_from() -> str:
    return _env("SMTP_FROM") or _env("SMTP_USER")


def smtp_password() -> str:
    # App passwords are often copied with spaces — normalize.
    return _env("SMTP_PASSWORD").replace(" ", "")


def smtp_host() -> str:
    provider = _env("SMTP_PROVIDER", "gmail").lower()
    if provider in {"gmail", "google"} and not _env("SMTP_HOST"):
        return GMAIL_SMTP_HOST
    return _env("SMTP_HOST") or GMAIL_SMTP_HOST


def smtp_port() -> int:
    raw = _env("SMTP_PORT")
    if raw:
        return int(raw)
    return GMAIL_SMTP_PORT


def smtp_configured() -> bool:
    """True when we have enough settings to attempt a real SMTP send."""
    return bool(smtp_from() and smtp_user() and smtp_password())


def auth_dev_show_otp() -> bool:
    """Include debug_code in API responses for local demos when enabled / SMTP missing."""
    flag = _env("AUTH_DEV_SHOW_OTP").lower()
    if flag in {"1", "true", "yes"}:
        return True
    if flag in {"0", "false", "no"}:
        return False
    return not smtp_configured()


def send_otp_email(to_email: str, code: str, *, purpose: str) -> None:
    """Send an OTP email via SMTP. Raises RuntimeError on failure when SMTP is configured."""
    subject = (
        "Your Axion verification code"
        if purpose == "email_verify"
        else "Your Axion password reset code"
    )
    body = (
        f"Your Axion code is: {code}\n\n"
        f"It expires in 10 minutes.\n"
        f"If you did not request this, you can ignore this email.\n"
    )

    if not smtp_configured():
        logger.warning(
            "SMTP not configured — OTP for %s (%s) logged only: %s",
            to_email,
            purpose,
            code,
        )
        return

    host = smtp_host()
    port = smtp_port()
    user = smtp_user()
    password = smtp_password()
    from_addr = smtp_from()
    use_tls = _env("SMTP_TLS", "1").lower() not in {"0", "false", "no"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls(context=context)
                smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(msg)
        logger.info("OTP email sent to %s (%s) via %s", to_email, purpose, host)
    except Exception as exc:  # noqa: BLE001 — surface as HTTP 503 upstream
        raise RuntimeError(
            "Failed to send email via SMTP. "
            "For Gmail, use an App Password (not your normal password) and "
            f"ensure SMTP_USER/SMTP_FROM match that account. Detail: {exc}"
        ) from exc


def smtp_status() -> dict:
    """Public-ish diagnostics for /auth/config (no secrets)."""
    return {
        "smtp_configured": smtp_configured(),
        "smtp_provider": _env("SMTP_PROVIDER", "gmail") or "gmail",
        "smtp_host": smtp_host() if smtp_configured() else None,
        "smtp_from": smtp_from() if smtp_configured() else None,
        "dev_show_otp": auth_dev_show_otp(),
    }
