"""Send one test OTP via Gmail SMTP using values from .env."""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

from backend.email_service import send_otp_email, smtp_configured, smtp_from, smtp_status

def main() -> None:
    status = smtp_status()
    print("smtp_status:", status)
    if not smtp_configured():
        raise SystemExit("SMTP not configured — set SMTP_USER / SMTP_PASSWORD / SMTP_FROM in .env")
    to = smtp_from()
    send_otp_email(to, "123456", purpose="email_verify")
    print(f"OK — sent test OTP email to {to}. Check inbox + Spam.")


if __name__ == "__main__":
    main()
