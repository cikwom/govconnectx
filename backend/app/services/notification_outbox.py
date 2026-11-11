import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_

from app.database import SessionLocal
from app.models.notification_delivery import NotificationDelivery
from app.services.email_delivery import send_notification_email
from app.services.sms_delivery import send_sms

logger = logging.getLogger(__name__)
LOCK_TIMEOUT = timedelta(minutes=5)


def enqueue_delivery(db, background_tasks, *, recipient_user_id: int, channel: str, destination: str, message: str, subject: str | None = None) -> NotificationDelivery:
    delivery = NotificationDelivery(
        recipient_user_id=recipient_user_id,
        channel=channel,
        destination=destination,
        subject=subject,
        message=message,
        status="queued",
        attempts=0,
        max_attempts=5,
        next_attempt_at=datetime.now(timezone.utc),
    )
    db.add(delivery)
    db.flush()
    if background_tasks is not None:
        background_tasks.add_task(deliver_notification_delivery, delivery.id)
    return delivery


def deliver_notification_delivery(delivery_id: int) -> bool:
    """Claim one outbox row, attempt delivery once, and persist its retry state."""
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        delivery = (
            db.query(NotificationDelivery)
            .filter(NotificationDelivery.id == delivery_id)
            .with_for_update()
            .first()
        )
        if delivery is None or delivery.status in ("sent", "failed"):
            return False
        locked_at = delivery.locked_at
        if locked_at is not None and locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        if delivery.status == "sending" and locked_at and now - locked_at < LOCK_TIMEOUT:
            return False
        next_attempt = delivery.next_attempt_at
        if next_attempt.tzinfo is None:
            next_attempt = next_attempt.replace(tzinfo=timezone.utc)
        if delivery.status == "queued" and next_attempt > now:
            return False
        if delivery.attempts >= delivery.max_attempts:
            delivery.status = "failed"
            delivery.last_error = "Maximum delivery attempts reached"
            delivery.locked_at = None
            db.commit()
            return False

        delivery.status = "sending"
        delivery.attempts += 1
        delivery.locked_at = now
        delivery.updated_at = now
        channel = delivery.channel
        destination = delivery.destination
        subject = delivery.subject
        message = delivery.message
        attempts = delivery.attempts
        db.commit()
    finally:
        db.close()

    try:
        if channel == "email":
            succeeded = send_notification_email(destination, subject or "GovConnect update", message)
        elif channel == "sms":
            succeeded = send_sms(destination, message)
        else:
            logger.error("Unsupported notification delivery channel: %s", channel)
            succeeded = False
    except Exception:
        logger.exception("Unexpected notification delivery failure for outbox id %s", delivery_id)
        succeeded = False

    db = SessionLocal()
    try:
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if delivery is None:
            return succeeded
        now = datetime.now(timezone.utc)
        delivery.locked_at = None
        delivery.updated_at = now
        if succeeded:
            delivery.status = "sent"
            delivery.sent_at = now
            delivery.last_error = None
        elif attempts >= delivery.max_attempts:
            delivery.status = "failed"
            delivery.last_error = "Provider delivery failed after maximum attempts"
        else:
            delay_seconds = min(30 * (2 ** (attempts - 1)), 3600)
            delivery.status = "queued"
            delivery.next_attempt_at = now + timedelta(seconds=delay_seconds)
            delivery.last_error = "Provider delivery failed or is not configured"
        db.commit()
        return succeeded
    finally:
        db.close()


def process_due_deliveries(batch_size: int = 25) -> int:
    """Retry queued deliveries and reclaim jobs abandoned by a crashed worker."""
    now = datetime.now(timezone.utc)
    stale_before = now - LOCK_TIMEOUT
    db = SessionLocal()
    try:
        rows = (
            db.query(NotificationDelivery.id)
            .filter(
                or_(
                    (NotificationDelivery.status == "queued") & (NotificationDelivery.next_attempt_at <= now),
                    (NotificationDelivery.status == "sending") & (NotificationDelivery.locked_at <= stale_before),
                )
            )
            .order_by(NotificationDelivery.created_at.asc())
            .limit(max(1, min(batch_size, 100)))
            .all()
        )
        ids = [row.id for row in rows]
    finally:
        db.close()

    processed = 0
    for delivery_id in ids:
        if deliver_notification_delivery(delivery_id):
            processed += 1
    return processed
