from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.notifications import NotificationResponse

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

@router.get("", response_model=list[NotificationResponse])
def list_notifications(unread_only: bool = False, limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    limit, offset = min(max(limit, 1), 100), max(offset, 0)
    preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if preference is not None and not preference.in_app_notifications:
        return []
    query = db.query(Notification).filter(Notification.recipient_user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if preference is not None and not preference.in_app_notifications:
        return {"unread_count": 0}
    count = db.query(Notification).filter(Notification.recipient_user_id == current_user.id, Notification.is_read.is_(False)).count()
    return {"unread_count": count}

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Notification).filter(Notification.id == notification_id, Notification.recipient_user_id == current_user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not item.is_read:
        item.is_read, item.read_at = True, datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item

@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.recipient_user_id == current_user.id, Notification.is_read.is_(False)).update({"is_read": True, "read_at": datetime.now(timezone.utc)}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read"}
