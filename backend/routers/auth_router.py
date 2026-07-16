"""Auth endpoints: register, login, OTP, password reset, Google (SDS §10.1)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import (
    User,
    create_access_token,
    create_reset_token,
    create_user,
    decode_reset_token,
    get_current_user,
    get_google_client_id,
    get_user_by_email,
    is_valid_email,
    mark_email_verified,
    password_validation_error,
    update_password,
    upsert_google_user,
    verify_password,
)
from backend.email_service import auth_dev_show_otp, send_otp_email, smtp_status
from backend.otp_store import OTP_TTL_SECONDS, issue_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])

PURPOSE_EMAIL_VERIFY = "email_verify"
PURPOSE_PASSWORD_RESET = "password_reset"


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str = ""


class UserResponse(BaseModel):
    user_id: str
    email: str
    created_at: str
    name: str = ""
    email_verified: bool = False


class EmailRequest(BaseModel):
    email: str


class ResendOtpRequest(BaseModel):
    email: str
    purpose: str  # email_verify | password_reset


class VerifyOtpRequest(BaseModel):
    email: str
    code: str
    purpose: str  # email_verify | password_reset


class ResetPasswordRequest(BaseModel):
    reset_token: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class OtpSentResponse(BaseModel):
    message: str
    expires_in: int = OTP_TTL_SECONDS
    debug_code: str | None = None
    email_sent: bool = False


class VerifyOtpPasswordResetResponse(BaseModel):
    reset_token: str
    message: str = "OTP verified"


class AuthConfigResponse(BaseModel):
    google_client_id: str | None = None
    google_enabled: bool = False
    smtp_configured: bool = False
    smtp_provider: str = "gmail"
    smtp_host: str | None = None
    smtp_from: str | None = None
    dev_show_otp: bool = True


def _validate_email(email: str) -> None:
    if not is_valid_email(email):
        raise HTTPException(
            status_code=422,
            detail="Enter a valid email address, e.g. name@gmail.com or name@university.edu.",
        )


def _validate_credentials(email: str, password: str) -> None:
    _validate_email(email)
    err = password_validation_error(password)
    if err:
        raise HTTPException(status_code=422, detail=err)


def _token_response(user: User) -> TokenResponse:
    token = create_access_token(user.user_id, user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        email=user.email,
        name=user.name,
    )


def _issue_and_send_otp(email: str, purpose: str) -> OtpSentResponse:
    code = issue_otp(email, purpose)
    mail_error: str | None = None
    email_sent = False
    try:
        send_otp_email(email, code, purpose=purpose)
        email_sent = True
    except RuntimeError as exc:
        mail_error = str(exc)

    show_debug = auth_dev_show_otp()
    if mail_error and not show_debug:
        # Production-like: surface SMTP failure when we aren't allowed to reveal the code.
        raise HTTPException(status_code=503, detail=mail_error)

    if email_sent:
        message = "If an account exists for that email, a code was sent."
    elif mail_error and show_debug:
        message = (
            "OTP was generated but Gmail SMTP rejected the login "
            "(check SMTP_PASSWORD — use a Google App Password, not your normal password)."
        )
    else:
        message = "OTP generated (SMTP not configured). Use debug_code for local testing."

    payload = OtpSentResponse(
        message=message,
        expires_in=OTP_TTL_SECONDS,
        email_sent=email_sent,
    )
    if show_debug:
        payload.debug_code = code
    return payload


def _verify_google_id_token(id_token: str) -> dict[str, Any]:
    client_id = get_google_client_id()
    if not client_id:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In is not configured. Set GOOGLE_CLIENT_ID on the server.",
        )
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="google-auth is not installed. Run: pip install google-auth",
        ) from exc

    try:
        return google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {exc}") from exc


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config() -> AuthConfigResponse:
    """Public frontend config (Google client id is not a secret)."""
    mail = smtp_status()
    client_id = get_google_client_id() or None
    return AuthConfigResponse(
        google_client_id=client_id,
        google_enabled=bool(client_id),
        smtp_configured=mail["smtp_configured"],
        smtp_provider=mail["smtp_provider"],
        smtp_host=mail["smtp_host"],
        smtp_from=mail["smtp_from"],
        dev_show_otp=mail["dev_show_otp"],
    )


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest) -> TokenResponse:
    _validate_credentials(body.email, body.password)
    if get_user_by_email(body.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user = create_user(body.email, body.password, name=body.name, email_verified=False)
    # Fire-and-surface OTP for email verification (used by /verify-code after signup).
    try:
        _issue_and_send_otp(user.email, PURPOSE_EMAIL_VERIFY)
    except HTTPException:
        # Account exists; verification can be resent from the verify page.
        pass
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    user = get_user_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=404, detail="No account found with that email.")
    if user.auth_provider == "google":
        raise HTTPException(
            status_code=401,
            detail="This account uses Google Sign-In. Continue with Google, or reset a password first.",
        )
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    return _token_response(user)


@router.post("/forgot-password", response_model=OtpSentResponse)
async def forgot_password(body: EmailRequest) -> OtpSentResponse:
    _validate_email(body.email)
    user = get_user_by_email(body.email)
    # Always return a generic message (no email enumeration).
    generic = OtpSentResponse(
        message="If an account exists for that email, a code was sent.",
        expires_in=OTP_TTL_SECONDS,
    )
    if user is None:
        return generic
    return _issue_and_send_otp(user.email, PURPOSE_PASSWORD_RESET)


@router.post("/resend-otp", response_model=OtpSentResponse)
async def resend_otp(body: ResendOtpRequest) -> OtpSentResponse:
    """Resend OTP for signup verification or password reset."""
    _validate_email(body.email)
    if body.purpose not in {PURPOSE_EMAIL_VERIFY, PURPOSE_PASSWORD_RESET}:
        raise HTTPException(status_code=422, detail="Invalid OTP purpose.")
    user = get_user_by_email(body.email)
    generic = OtpSentResponse(
        message="If an account exists for that email, a code was sent.",
        expires_in=OTP_TTL_SECONDS,
    )
    if user is None:
        return generic
    if body.purpose == PURPOSE_EMAIL_VERIFY and user.email_verified:
        return OtpSentResponse(message="Email is already verified.", expires_in=0)
    return _issue_and_send_otp(user.email, body.purpose)


@router.post("/verify-otp")
async def verify_otp_endpoint(body: VerifyOtpRequest) -> dict:
    _validate_email(body.email)
    if body.purpose not in {PURPOSE_EMAIL_VERIFY, PURPOSE_PASSWORD_RESET}:
        raise HTTPException(status_code=422, detail="Invalid OTP purpose.")
    code = (body.code or "").strip()
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=422, detail="Enter the 6-digit code.")

    user = get_user_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired code.")

    if not verify_otp(body.email, body.purpose, code):
        raise HTTPException(status_code=401, detail="Invalid or expired code.")

    if body.purpose == PURPOSE_EMAIL_VERIFY:
        user = mark_email_verified(body.email) or user
        token = _token_response(user)
        return {
            "purpose": PURPOSE_EMAIL_VERIFY,
            "access_token": token.access_token,
            "token_type": token.token_type,
            "user_id": token.user_id,
            "email": token.email,
            "name": token.name,
            "message": "Email verified",
        }

    reset_token = create_reset_token(user.email)
    return VerifyOtpPasswordResetResponse(reset_token=reset_token).model_dump()


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest) -> dict:
    err = password_validation_error(body.password)
    if err:
        raise HTTPException(status_code=422, detail=err)
    email = decode_reset_token(body.reset_token)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid or expired reset token.")
    user = update_password(email, body.password)
    if user is None:
        raise HTTPException(status_code=404, detail="No account found with that email.")
    return {"message": "Password updated."}


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest) -> TokenResponse:
    claims = _verify_google_id_token(body.id_token)
    email = claims.get("email")
    if not email or not claims.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Google account email is missing or unverified.")
    name = (claims.get("name") or "").strip()
    user = upsert_google_user(email=email, name=name)
    return _token_response(user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        created_at=current_user.created_at,
        name=current_user.name,
        email_verified=current_user.email_verified,
    )


@router.post("/logout")
async def logout() -> dict:
    return {"message": "logged out"}
