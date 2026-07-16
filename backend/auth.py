"""JWT authentication: user model, password hashing, token issuance (SDS §10.1)."""

from __future__ import annotations

import json
import os
import re
import secrets
import uuid
import warnings
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_DB_PATH = DATA_DIR / "users.db.json"

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 24 * 60
RESET_TOKEN_EXPIRE_MINUTES = 15

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = "dev-secret-change-in-prod"
    warnings.warn(
        "JWT_SECRET is not set; falling back to an insecure default secret. "
        "Set the JWT_SECRET environment variable in production.",
        stacklevel=2,
    )

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class User:
    user_id: str
    email: str
    hashed_password: str
    created_at: str
    name: str = ""
    email_verified: bool = False
    auth_provider: str = "password"  # password | google | both


_USER_FIELD_NAMES = {f.name for f in fields(User)}


def load_users() -> dict[str, User]:
    if not USERS_DB_PATH.exists():
        return {}
    raw = json.loads(USERS_DB_PATH.read_text(encoding="utf-8") or "{}")
    users: dict[str, User] = {}
    for email, data in raw.items():
        payload = {
            "name": "",
            "email_verified": False,
            "auth_provider": "password",
            **{k: v for k, v in data.items() if k in _USER_FIELD_NAMES},
        }
        users[email] = User(**payload)
    return users


def save_users(users: dict[str, User]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = {email: asdict(user) for email, user in users.items()}
    USERS_DB_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def get_user_by_email(email: str) -> User | None:
    return load_users().get(email.strip().lower())


def create_user(email: str, password: str, name: str = "", *, email_verified: bool = False) -> User:
    users = load_users()
    normalized_email = email.strip().lower()
    user = User(
        user_id=str(uuid.uuid4()),
        email=normalized_email,
        hashed_password=hash_password(password),
        created_at=datetime.now(timezone.utc).isoformat(),
        name=(name or "").strip(),
        email_verified=email_verified,
        auth_provider="password",
    )
    users[normalized_email] = user
    save_users(users)
    return user


def upsert_google_user(*, email: str, name: str = "") -> User:
    """Create or update a user authenticated via Google ID token."""
    users = load_users()
    normalized_email = email.strip().lower()
    existing = users.get(normalized_email)
    if existing is None:
        user = User(
            user_id=str(uuid.uuid4()),
            email=normalized_email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            created_at=datetime.now(timezone.utc).isoformat(),
            name=(name or "").strip(),
            email_verified=True,
            auth_provider="google",
        )
    else:
        provider = "both" if existing.auth_provider in {"password", "both"} else "google"
        user = User(
            user_id=existing.user_id,
            email=existing.email,
            hashed_password=existing.hashed_password,
            created_at=existing.created_at,
            name=(name or existing.name or "").strip(),
            email_verified=True,
            auth_provider=provider,
        )
    users[normalized_email] = user
    save_users(users)
    return user


def mark_email_verified(email: str) -> User | None:
    users = load_users()
    normalized = email.strip().lower()
    user = users.get(normalized)
    if user is None:
        return None
    user.email_verified = True
    users[normalized] = user
    save_users(users)
    return user


def update_password(email: str, new_password: str) -> User | None:
    users = load_users()
    normalized = email.strip().lower()
    user = users.get(normalized)
    if user is None:
        return None
    provider = "both" if user.auth_provider == "google" else user.auth_provider
    user.hashed_password = hash_password(new_password)
    user.auth_provider = provider or "password"
    users[normalized] = user
    save_users(users)
    return user


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "user_id": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    payload = {
        "type": "password_reset",
        "email": email.strip().lower(),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_reset_token(token: str) -> str | None:
    """Return email if reset token is valid, else None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "password_reset":
        return None
    email = payload.get("email")
    return email if isinstance(email, str) and email else None


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email = payload.get("email")
    if email is None:
        raise credentials_exception
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user
