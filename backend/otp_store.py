"""One-time passcodes for email verification and password reset."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

OTP_TTL_SECONDS = 10 * 60
OTP_LENGTH = 6

DATA_DIR = Path(__file__).resolve().parent / "data"
OTP_DB_PATH = DATA_DIR / "otp.db.json"


@dataclass
class OtpRecord:
    email: str
    purpose: str  # email_verify | password_reset
    code_hash: str
    expires_at: str
    attempts: int = 0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def load_otps() -> dict[str, OtpRecord]:
    if not OTP_DB_PATH.exists():
        return {}
    raw = json.loads(OTP_DB_PATH.read_text(encoding="utf-8") or "{}")
    return {key: OtpRecord(**data) for key, data in raw.items()}


def save_otps(otps: dict[str, OtpRecord]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OTP_DB_PATH.write_text(
        json.dumps({k: asdict(v) for k, v in otps.items()}, indent=2),
        encoding="utf-8",
    )


def _key(email: str, purpose: str) -> str:
    return f"{email.strip().lower()}::{purpose}"


def generate_otp_code() -> str:
    # Cryptographically strong numeric code (includes leading zeros).
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def issue_otp(email: str, purpose: str) -> str:
    """Create/replace an OTP for email+purpose. Returns the plaintext code."""
    code = generate_otp_code()
    otps = load_otps()
    otps[_key(email, purpose)] = OtpRecord(
        email=email.strip().lower(),
        purpose=purpose,
        code_hash=_hash_code(code),
        expires_at=(_now() + timedelta(seconds=OTP_TTL_SECONDS)).isoformat(),
        attempts=0,
    )
    save_otps(otps)
    return code


def verify_otp(email: str, purpose: str, code: str, *, max_attempts: int = 5) -> bool:
    otps = load_otps()
    key = _key(email, purpose)
    record = otps.get(key)
    if record is None:
        return False
    expires = datetime.fromisoformat(record.expires_at)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if _now() > expires:
        otps.pop(key, None)
        save_otps(otps)
        return False
    if record.attempts >= max_attempts:
        otps.pop(key, None)
        save_otps(otps)
        return False
    record.attempts += 1
    ok = secrets.compare_digest(record.code_hash, _hash_code(code.strip()))
    if ok:
        otps.pop(key, None)
        save_otps(otps)
        return True
    otps[key] = record
    save_otps(otps)
    return False


def clear_otp(email: str, purpose: str) -> None:
    otps = load_otps()
    otps.pop(_key(email, purpose), None)
    save_otps(otps)
