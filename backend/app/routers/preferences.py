from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.user_preference import UserPreference
from app.models.user import User
from app.schemas.preferences import UserPreferenceResponse, UserPreferenceUpdate

router = APIRouter(prefix="/api/v1/preferences", tags=["User preferences"])


def get_or_create_preference(db: Session, user_id: int) -> UserPreference:
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if preference is None:
        preference = UserPreference(user_id=user_id)
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference


@router.get("", response_model=UserPreferenceResponse)
def read_preferences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_or_create_preference(db, current_user.id)


@router.put("", response_model=UserPreferenceResponse)
def update_preferences(payload: UserPreferenceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    preference = get_or_create_preference(db, current_user.id)
    preference.email_notifications = payload.email_notifications
    preference.in_app_notifications = payload.in_app_notifications
    preference.preferred_language = payload.preferred_language
    preference.updated_at = datetime.now(timezone.utc)
    record_audit_event(db, actor_user_id=current_user.id, action="user.preferences_updated", entity_type="user", entity_id=current_user.id, summary="User updated notification and language preferences", details={"email_notifications": payload.email_notifications, "in_app_notifications": payload.in_app_notifications, "preferred_language": payload.preferred_language})
    db.commit()
    db.refresh(preference)
    return preference
