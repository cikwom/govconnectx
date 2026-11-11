import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from app.database import Base


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        Index("ix_notification_deliveries_due", "status", "next_attempt_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(String(12), nullable=False, index=True)
    destination = Column(String(255), nullable=False)
    subject = Column(String(180), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(16), nullable=False, default="queued", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String(300), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime(timezone=True), nullable=True)
