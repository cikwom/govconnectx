import logging
import os

import httpx
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_preference import UserPreference

logger = logging.getLogger(__name__)


def send_sms(phone_number: str, message: str) -> bool:
    """Send an SMS through Termii; fail closed when the provider is not configured."""
    api_key = os.getenv("TERMII_API_KEY")
    sender_id = os.getenv("TERMII_SENDER_ID")
    if not api_key or not sender_id:
        logger.warning("SMS delivery skipped because Termii is not configured")
        return False

    endpoint = os.getenv("TERMII_API_URL", "https://api.ng.termii.com/api/sms/send")
    timeout = float(os.getenv("SMS_TIMEOUT_SECONDS", "10"))
    payload = {
        "api_key": api_key,
        "to": phone_number,
        "from": sender_id,
        "sms": message[:1000],
        "type": "plain",
        "channel": "generic",
    }
    try:
        response = httpx.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if str(result.get("code", "")).lower() != "ok":
            logger.warning("Termii did not accept an SMS request")
            return False
        return True
    except (httpx.HTTPError, ValueError):
        logger.exception("Could not deliver GovConnectX SMS")
        return False


def queue_notification_sms(db: Session, background_tasks, recipient_user_id: int, message: str) -> None:
    """Queue an update only for an active, verified number with current SMS consent."""
    user = db.query(User).filter(
        User.id == recipient_user_id,
        User.is_active.is_(True),
        User.phone_verified_at.isnot(None),
        User.phone_number.isnot(None),
    ).first()
    if user is None:
        return
    preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if (
        preference is None
        or not preference.sms_notifications
        or preference.sms_consent_at is None
        or preference.sms_consent_revoked_at is not None
    ):
        return
    background_tasks.add_task(send_sms, user.phone_number, message)
