"""JWT authentication: user model, password hashing, token issuance (SDS §10.1)."""

from __future__ import annotations

import json
import os
import re
import uuid
import warnings
from dataclasses import asdict, dataclass
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

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = "dev-secret-change-in-prod"
    warnings.warn(
        "JWT_SECRET is not set; falling back to an insecure default secret. "
        "Set the JWT_SECRET environment variable in production.",
        stacklevel=2,
    )

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class User:
    user_id: str
    email: str
    hashed_password: str
    created_at: str


def load_users() -> dict[str, User]:
    if not USERS_DB_PATH.exists():
        return {}
    raw = json.loads(USERS_DB_PATH.read_text(encoding="utf-8") or "{}")
    return {email: User(**data) for email, data in raw.items()}


def save_users(users: dict[str, User]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = {email: asdict(user) for email, user in users.items()}
    USERS_DB_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def get_user_by_email(email: str) -> User | None:
    return load_users().get(email.strip().lower())


def create_user(email: str, password: str) -> User:
    users = load_users()
    normalized_email = email.strip().lower()
    user = User(
        user_id=str(uuid.uuid4()),
        email=normalized_email,
        hashed_password=hash_password(password),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    users[normalized_email] = user
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
