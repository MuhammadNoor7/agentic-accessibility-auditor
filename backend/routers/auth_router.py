"""Auth endpoints: register, login, me, logout (SDS §10.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import (
    EMAIL_RE,
    User,
    create_access_token,
    create_user,
    get_current_user,
    get_user_by_email,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    created_at: str


def _validate_credentials(email: str, password: str) -> None:
    if not EMAIL_RE.match((email or "").strip()):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if not password or len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest) -> TokenResponse:
    _validate_credentials(body.email, body.password)
    if get_user_by_email(body.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user = create_user(body.email, body.password)
    token = create_access_token(user.user_id, user.email)
    return TokenResponse(access_token=token, user_id=user.user_id, email=user.email)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    user = get_user_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=404, detail="No account found with that email.")
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    token = create_access_token(user.user_id, user.email)
    return TokenResponse(access_token=token, user_id=user.user_id, email=user.email)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        created_at=current_user.created_at,
    )


@router.post("/logout")
async def logout() -> dict:
    return {"message": "logged out"}
