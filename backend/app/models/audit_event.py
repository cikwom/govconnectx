import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class AuditEvent(Base):
    """Append-only application audit event. No public write or delete endpoint exists."""

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    summary = Column(String(500), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


def record_audit_event(db, *, actor_user_id, action, entity_type, entity_id=None, summary, details=None):
    """Add a minimal audit record to the caller's transaction; never store credentials or evidence."""
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary[:500],
        details_json=json.dumps(details, separators=(",", ":"), sort_keys=True) if details else None,
    )
    db.add(event)
    return event
