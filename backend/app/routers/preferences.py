import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import JWT_SECRET
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.phone_verification import PhoneVerification
from app.models.user_preference import UserPreference
from app.models.user import User
from app.schemas.preferences import (
    PhoneVerificationConfirm,
    PhoneVerificationRequest,
    UserPreferenceResponse,
    UserPreferenceUpdate,
)
from app.services.sms_delivery import send_sms

router = APIRouter(prefix="/api/v1/preferences", tags=["User preferences"])


def get_or_create_preference(db: Session, user_id: int) -> UserPreference:
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if preference is None:
        preference = UserPreference(user_id=user_id)
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference


def preference_response(preference: UserPreference, user: User) -> dict:
    return {
        "email_notifications": preference.email_notifications,
        "in_app_notifications": preference.in_app_notifications,
        "sms_notifications": preference.sms_notifications,
        "sms_consent_at": preference.sms_consent_at,
        "sms_consent_revoked_at": preference.sms_consent_revoked_at,
        "preferred_language": preference.preferred_language,
        "phone_number": user.phone_number,
        "phone_verified_at": user.phone_verified_at,
        "updated_at": preference.updated_at,
    }


def verification_digest(code: str) -> str:
    return hmac.new(JWT_SECRET.encode("utf-8"), code.encode("ascii"), hashlib.sha256).hexdigest()


@router.get("", response_model=UserPreferenceResponse)
def read_preferences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    preference = get_or_create_preference(db, current_user.id)
    return preference_response(preference, current_user)


@router.put("", response_model=UserPreferenceResponse)
def update_preferences(payload: UserPreferenceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    preference = get_or_create_preference(db, current_user.id)
    preference.email_notifications = payload.email_notifications
    preference.in_app_notifications = payload.in_app_notifications
    preference.preferred_language = payload.preferred_language
    now = datetime.now(timezone.utc)

    if payload.sms_notifications is True:
        if not current_user.phone_number or current_user.phone_verified_at is None:
            raise HTTPException(status_code=400, detail="Verify your phone number before enabling SMS notifications")
        if not preference.sms_notifications or preference.sms_consent_revoked_at is not None:
            preference.sms_consent_at = now
            preference.sms_consent_revoked_at = None
        preference.sms_notifications = True
    elif payload.sms_notifications is False and preference.sms_notifications:
        preference.sms_notifications = False
        preference.sms_consent_revoked_at = now

    preference.updated_at = now
    record_audit_event(
        db,
        actor_user_id=current_user.id,
        action="user.preferences_updated",
        entity_type="user",
        entity_id=current_user.id,
        summary="User updated notification and language preferences",
        details={
            "email_notifications": payload.email_notifications,
            "in_app_notifications": payload.in_app_notifications,
            "sms_notifications": preference.sms_notifications,
            "preferred_language": payload.preferred_language,
        },
    )
    db.commit()
    db.refresh(preference)
    return preference_response(preference, current_user)


@router.post("/phone/request-verification")
def request_phone_verification(
    payload: PhoneVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    phone_number = payload.phone_number
    if current_user.phone_number == phone_number and current_user.phone_verified_at is not None:
        raise HTTPException(status_code=409, detail="This phone number is already verified")

    existing = db.query(User).filter(
        User.phone_number == phone_number,
        User.id != current_user.id,
    ).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="This phone number is already associated with another account")

    now = datetime.now(timezone.utc)
    recent = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == current_user.id,
        PhoneVerification.created_at >= now - timedelta(hours=1),
    ).count()
    if recent >= 5:
        raise HTTPException(status_code=429, detail="Too many verification requests. Try again later.")

    latest = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == current_user.id,
    ).order_by(PhoneVerification.created_at.desc()).first()
    if latest is not None:
        created_at = latest.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if now - created_at < timedelta(seconds=60):
            raise HTTPException(status_code=429, detail="Wait one minute before requesting another verification code.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    if not send_sms(phone_number, f"Your GovConnect verification code is {code}. It expires in 10 minutes. Do not share this code."):
        raise HTTPException(status_code=503, detail="SMS verification is temporarily unavailable. Please try again later.")

    current_user.phone_number = phone_number
    current_user.phone_verified_at = None
    preference = get_or_create_preference(db, current_user.id)
    if preference.sms_notifications:
        preference.sms_notifications = False
        preference.sms_consent_revoked_at = now

    db.query(PhoneVerification).filter(
        PhoneVerification.user_id == current_user.id,
        PhoneVerification.consumed_at.is_(None),
    ).update({"consumed_at": now}, synchronize_session=False)
    challenge = PhoneVerification(
        user_id=current_user.id,
        phone_number=phone_number,
        code_hash=verification_digest(code),
        attempts=0,
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    db.add(challenge)
    db.commit()
    record_audit_event(
        db,
        actor_user_id=current_user.id,
        action="user.phone_verification_requested",
        entity_type="user",
        entity_id=current_user.id,
        summary="User requested phone verification",
        details={"phone_suffix": phone_number[-4:]},
    )
    db.commit()
    return {"message": "A verification code has been sent. It expires in 10 minutes."}


@router.post("/phone/verify")
def verify_phone(
    payload: PhoneVerificationConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    challenge = db.query(PhoneVerification).filter(
        PhoneVerification.user_id == current_user.id,
        PhoneVerification.phone_number == current_user.phone_number,
        PhoneVerification.consumed_at.is_(None),
    ).order_by(PhoneVerification.created_at.desc()).first()
    if challenge is None:
        raise HTTPException(status_code=400, detail="Request a new phone verification code first")

    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        challenge.consumed_at = now
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code expired. Request a new code.")

    if challenge.attempts >= 5:
        challenge.consumed_at = now
        db.commit()
        raise HTTPException(status_code=429, detail="Too many incorrect codes. Request a new code.")

    challenge.attempts += 1
    if not hmac.compare_digest(challenge.code_hash, verification_digest(payload.code)):
        if challenge.attempts >= 5:
            challenge.consumed_at = now
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect verification code")

    challenge.consumed_at = now
    current_user.phone_verified_at = now
    record_audit_event(
        db,
        actor_user_id=current_user.id,
        action="user.phone_verified",
        entity_type="user",
        entity_id=current_user.id,
        summary="User verified a phone number",
        details={"phone_suffix": (current_user.phone_number or "")[-4:]},
    )
    db.commit()
    return {"message": "Phone number verified. You can now choose to enable SMS notifications."}
