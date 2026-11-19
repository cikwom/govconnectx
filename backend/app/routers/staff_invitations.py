import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.department import Department
from app.models.location import LocalGovernmentArea, State
from app.models.staff_invitation import StaffInvitation
from app.models.user import User
from app.services.email_delivery import send_notification_email

router = APIRouter(prefix="/api/v1", tags=["Staff invitations"])
STAFF_ROLES = {"official", "supervisor", "department_admin"}
INVITATION_TTL_HOURS = 72


class StaffInvitationCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=2, max_length=150)
    role: str
    department_id: int | None = None
    home_state_code: str | None = Field(default=None, max_length=12)
    home_lga_code: str | None = Field(default=None, max_length=16)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("A valid email address is required")
        return value

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.split())


class StaffInvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=200)
    password: str = Field(min_length=12, max_length=128)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


@router.post("/admin/staff-invitations", status_code=status.HTTP_201_CREATED)
def create_staff_invitation(
    payload: StaffInvitationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("system_admin")),
):
    email = payload.email
    role = payload.role.strip().lower()
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=422, detail="Only official, supervisor or department administrator roles can be invited")
    if len(payload.full_name.strip()) < 2:
        raise HTTPException(status_code=422, detail="Full name must contain at least 2 characters")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account already uses this email address")
    if db.query(StaffInvitation).filter(
        StaffInvitation.email == email,
        StaffInvitation.accepted_at.is_(None),
        StaffInvitation.revoked_at.is_(None),
        StaffInvitation.expires_at > datetime.now(timezone.utc),
    ).first():
        raise HTTPException(status_code=409, detail="An active invitation already exists for this email address")
    if payload.department_id is not None and db.get(Department, payload.department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    if bool(payload.home_state_code) != bool(payload.home_lga_code):
        raise HTTPException(status_code=422, detail="Select both State and LGA")
    if payload.home_state_code:
        state = db.get(State, payload.home_state_code.strip().upper())
        lga = db.get(LocalGovernmentArea, payload.home_lga_code.strip().upper())
        if state is None or lga is None or lga.state_code != state.code:
            raise HTTPException(status_code=422, detail="The selected LGA does not belong to the selected State")

    now = datetime.now(timezone.utc)
    raw_token = secrets.token_urlsafe(40)
    invitation = StaffInvitation(
        email=email,
        full_name=payload.full_name.strip(),
        role=role,
        department_id=payload.department_id,
        home_state_code=payload.home_state_code.strip().upper() if payload.home_state_code else None,
        home_lga_code=payload.home_lga_code.strip().upper() if payload.home_lga_code else None,
        token_hash=_digest(raw_token),
        invited_by_user_id=actor.id,
        expires_at=now + timedelta(hours=INVITATION_TTL_HOURS),
    )
    db.add(invitation)
    db.flush()
    record_audit_event(
        db, actor_user_id=actor.id, action="staff.invitation_created",
        entity_type="staff_invitation", entity_id=invitation.id,
        summary="System administrator invited a staff member",
        details={"email": email, "role": role, "department_id": payload.department_id, "expires_at": invitation.expires_at.isoformat()},
    )
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    invitation_url = f"{frontend_url}/staff-invitation?token={raw_token}"
    background_tasks.add_task(
        send_notification_email, email, "Your GovConnectX staff invitation",
        f"Hello {payload.full_name.strip()},\n\nYou have been invited to join GovConnectX as {role.replace('_', ' ')}. "
        f"Use this single-use link within {INVITATION_TTL_HOURS} hours to set your password:\n\n{invitation_url}\n\n"
        "If you were not expecting this invitation, you can ignore this email.",
    )
    response = {
        "id": invitation.id, "email": invitation.email, "role": invitation.role,
        "department_id": invitation.department_id, "expires_at": invitation.expires_at.isoformat(),
        "email_delivery": "scheduled", "message": "Invitation created. Email delivery is attempted in the background.",
    }
    if os.getenv("ENVIRONMENT", "development").strip().lower() != "production":
        response["development_invitation_url"] = invitation_url
    return response


@router.get("/admin/staff-invitations")
def list_staff_invitations(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    now = datetime.now(timezone.utc)
    rows = db.query(StaffInvitation).order_by(StaffInvitation.created_at.desc()).limit(100).all()
    return {"items": [{
        "id": row.id, "email": row.email, "full_name": row.full_name, "role": row.role,
        "department_id": row.department_id, "expires_at": row.expires_at.isoformat(),
        "accepted_at": row.accepted_at.isoformat() if row.accepted_at else None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        "status": "accepted" if row.accepted_at else "revoked" if row.revoked_at else "expired" if _utc(row.expires_at) <= now else "pending",
        "created_at": row.created_at.isoformat() if row.created_at else None,
    } for row in rows]}


@router.post("/admin/staff-invitations/{invitation_id}/revoke")
def revoke_staff_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("system_admin")),
):
    invitation = db.query(StaffInvitation).filter(StaffInvitation.id == invitation_id).with_for_update().first()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.accepted_at is not None:
        raise HTTPException(status_code=409, detail="An accepted invitation cannot be revoked")
    if invitation.revoked_at is not None:
        return {"id": invitation.id, "status": "revoked"}
    invitation.revoked_at = datetime.now(timezone.utc)
    record_audit_event(
        db, actor_user_id=actor.id, action="staff.invitation_revoked",
        entity_type="staff_invitation", entity_id=invitation.id,
        summary="System administrator revoked a staff invitation",
        details={"email": invitation.email, "role": invitation.role},
    )
    db.commit()
    return {"id": invitation.id, "status": "revoked"}


@router.post("/staff-invitations/accept")
def accept_staff_invitation(payload: StaffInvitationAccept, db: Session = Depends(get_db)):
    invitation = db.query(StaffInvitation).filter(
        StaffInvitation.token_hash == _digest(payload.token)
    ).with_for_update().first()
    now = datetime.now(timezone.utc)
    if invitation is None or invitation.accepted_at is not None or invitation.revoked_at is not None or _utc(invitation.expires_at) <= now:
        raise HTTPException(status_code=400, detail="This invitation is invalid, expired or already used")
    if db.query(User).filter(User.email == invitation.email).first():
        raise HTTPException(status_code=409, detail="An account already uses this email address")
    user = User(
        email=invitation.email, full_name=invitation.full_name,
        password_hash=hash_password(payload.password), role=invitation.role,
        department_id=invitation.department_id, home_state_code=invitation.home_state_code,
        home_lga_code=invitation.home_lga_code, is_active=True,
    )
    db.add(user)
    invitation.accepted_at = now
    db.flush()
    record_audit_event(
        db, actor_user_id=invitation.invited_by_user_id, action="staff.invitation_accepted",
        entity_type="staff_invitation", entity_id=invitation.id,
        summary="A staff invitation was accepted and an account was activated",
        details={"email": invitation.email, "role": invitation.role, "user_id": user.id},
    )
    db.commit()
    db.refresh(user)
    return {"message": "Staff account activated. You can now sign in.", "user_id": user.id}


