from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_preferences_user"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email_notifications = Column(Boolean, nullable=False, default=True)
    sms_notifications = Column(Boolean, nullable=False, default=False)
    sms_consent_at = Column(DateTime(timezone=True), nullable=True)
    sms_consent_revoked_at = Column(DateTime(timezone=True), nullable=True)
    in_app_notifications = Column(Boolean, nullable=False, default=True)
    preferred_language = Column(String(8), nullable=False, default="en")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
