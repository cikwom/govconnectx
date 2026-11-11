import os
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.notification_delivery import NotificationDelivery
from app.models.phone_verification import PhoneVerification


def prune_expired_phone_verifications(db, *, now: datetime | None = None, retention_hours: int = 24) -> int:
    """Delete OTP challenge records after their short security/audit retention window."""
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(hours=max(1, retention_hours))
    return db.query(PhoneVerification).filter(PhoneVerification.created_at < cutoff).delete(synchronize_session=False)


def prune_notification_deliveries(db, *, now: datetime | None = None, retention_days: int | None = None) -> int:
    """Delete only terminal delivery records when an explicit retention period is configured."""
    configured = retention_days
    if configured is None:
        try:
            configured = int(os.getenv("NOTIFICATION_DELIVERY_RETENTION_DAYS", "0"))
        except ValueError:
            configured = 0
    if configured <= 0:
        return 0

    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(days=configured)
    return db.query(NotificationDelivery).filter(
        NotificationDelivery.status.in_(("sent", "failed")),
        NotificationDelivery.created_at < cutoff,
    ).delete(synchronize_session=False)


def run_retention_cleanup() -> dict[str, int]:
    db = SessionLocal()
    try:
        phone_challenges = prune_expired_phone_verifications(db)
        deliveries = prune_notification_deliveries(db)
        db.commit()
        return {
            "phone_verification_challenges": phone_challenges,
            "notification_deliveries": deliveries,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
