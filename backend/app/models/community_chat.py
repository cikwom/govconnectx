from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.database import Base


class CommunityChatMessage(Base):
    __tablename__ = "community_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    community_code = Column(String(32), ForeignKey("communities.code"), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0)
    author_user = relationship("User", foreign_keys=[author_user_id])

    __table_args__ = (
        Index("ix_community_chat_messages_room_created", "community_code", "created_at", "id"),
    )
