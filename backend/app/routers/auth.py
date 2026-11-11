import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.auth_security_event import AuthSecurityEvent
from app.models.location import LocalGovernmentArea, State
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RoleUpdateRequest, TokenResponse, UserResponse
from app.services.email_delivery import send_notification_email

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
RESET_TOKEN_TTL_MINUTES = 30
RESET_REQUEST_COOLDOWN_SECONDS = 60


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetComplete(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


def _client_details(request: Request) -> tuple[str | None, str | None]:
    # Do not trust arbitrary forwarded headers unless a trusted proxy is configured.
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:500] or None
    return ip_address, user_agent


def validate_home_location(payload: RegisterRequest, db: Session) -> None:
    if bool(payload.home_state_code) != bool(payload.home_lga_code):
        raise HTTPException(status_code=400, detail="Select both your state and local government area")
    if payload.home_state_code:
        state = db.get(State, payload.home_state_code)
        lga = db.get(LocalGovernmentArea, payload.home_lga_code)
        if state is None or lga is None or lga.state_code != state.code:
            raise HTTPException(status_code=400, detail="The selected local government area does not belong to that state")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        # Keep the response generic so public registration cannot be used to enumerate accounts.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to create an account with those details. Sign in or use password recovery if you already registered.")
    validate_home_location(payload, db)
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="citizen",
        home_state_code=payload.home_state_code,
        home_lga_code=payload.home_lga_code,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled")

    ip_address, user_agent = _client_details(request)
    db.add(AuthSecurityEvent(user_id=user.id, event_type="login_success", ip_address=ip_address, user_agent=user_agent))
    db.commit()
    background_tasks.add_task(
        send_notification_email,
        user.email,
        "New sign-in to your GovConnect account",
        f"A successful sign-in to your GovConnect account was recorded at {datetime.now(timezone.utc).isoformat()}. If this was not you, sign in, change your password and revoke other sessions.",
    )
    return TokenResponse(access_token=create_access_token(user.id, user.role, user.token_version), user=user)


@router.post("/password-reset/request")
def request_password_reset(payload: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Always return the same response to prevent account enumeration.
    generic_response = {"message": "If an account matches that email address, password recovery instructions will be sent."}
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if user is None:
        return generic_response

    now = datetime.now(timezone.utc)
    recent_request = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.created_at >= now - timedelta(seconds=RESET_REQUEST_COOLDOWN_SECONDS),
    ).first()
    if recent_request is not None:
        return generic_response

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
    )
    db.add(reset_token)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_url = f"{frontend_url}/reset-password?token={raw_token}"
    background_tasks.add_task(
        send_notification_email,
        user.email,
        "Reset your GovConnect password",
        f"Hello {user.full_name},\n\nA password reset was requested for your GovConnect account. Use this one-time link within {RESET_TOKEN_TTL_MINUTES} minutes:\n\n{reset_url}\n\nIf you did not request this, you can ignore this email. Your password will not change unless the link is used.",
    )
    return generic_response


@router.post("/password-reset/complete")
def complete_password_reset(payload: PasswordResetComplete, request: Request, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if reset_token is None or reset_token.used_at is not None:
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has expired. Request a new one.")
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has expired. Request a new one.")

    user = db.query(User).filter(User.id == reset_token.user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has expired. Request a new one.")

    reset_token.used_at = now
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    ip_address, user_agent = _client_details(request)
    db.add(AuthSecurityEvent(user_id=user.id, event_type="password_reset", ip_address=ip_address, user_agent=user_agent))
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_token.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now}, synchronize_session=False)
    db.commit()
    return {"message": "Your password has been reset. Please sign in again on your devices."}


@router.get("/security/activity")
def get_security_activity(limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    safe_limit = min(max(limit, 1), 50)
    events = db.query(AuthSecurityEvent).filter(
        AuthSecurityEvent.user_id == current_user.id,
    ).order_by(AuthSecurityEvent.created_at.desc()).limit(safe_limit).all()
    return [{
        "id": event.id,
        "event_type": event.event_type,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    } for event in events]


@router.post("/security/revoke-sessions")
def revoke_other_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.token_version += 1
    db.add(AuthSecurityEvent(user_id=current_user.id, event_type="sessions_revoked"))
    db.commit()
    return {"message": "All existing sessions have been signed out. Sign in again on this device."}


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, payload: RoleUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_roles("system_admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
