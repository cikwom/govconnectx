import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_notification_email(to_email: str, subject: str, body: str) -> bool:
    """Send a minimal notification email; missing provider configuration is a safe no-op."""
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER")
    if not host or not sender:
        logger.info("Email notification skipped because SMTP is not configured")
        return False

    message = EmailMessage()
    message["Subject"] = subject[:180]
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
        f"{body}\n\nOpen GovConnect Nigeria to review the update. "
        "Do not reply with passwords, verification codes or sensitive personal information."
    )

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    timeout = float(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() in ("1", "true", "yes")
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes")

    try:
        if use_ssl:
            client = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            client = smtplib.SMTP(host, port, timeout=timeout)
        with client:
            client.ehlo()
            if use_tls and not use_ssl:
                client.starttls()
                client.ehlo()
            if username and password:
                client.login(username, password)
            client.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("Could not deliver GovConnectX notification email")
        return False
