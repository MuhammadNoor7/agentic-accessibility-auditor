"""Outbound email helper for OTP codes (SMTP when configured)."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_FROM"))


def auth_dev_show_otp() -> bool:
    """When true (or SMTP missing), API responses may include debug_code for local demos/tests."""
    flag = os.environ.get("AUTH_DEV_SHOW_OTP", "").strip().lower()
    if flag in {"1", "true", "yes"}:
        return True
    # Default for local internship demos without SMTP.
    return not smtp_configured()


def send_otp_email(to_email: str, code: str, *, purpose: str) -> None:
    """Send an OTP email. Raises RuntimeError if SMTP is configured but sending fails."""
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

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ["SMTP_FROM"]
    use_tls = os.environ.get("SMTP_TLS", "1").strip().lower() not in {"0", "false", "no"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as exc:  # noqa: BLE001 — surface as HTTP 503 upstream
        raise RuntimeError(f"Failed to send email: {exc}") from exc
