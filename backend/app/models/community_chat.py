from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class CommunityChatMessage(Base):
    __tablename__ = "community_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    community_code = Column(String(32), ForeignKey("communities.code"), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    image_storage_key = Column(String(80), nullable=True)
    image_storage_backend = Column(String(16), nullable=True)
    image_content_type = Column(String(100), nullable=True)
    image_original_filename = Column(String(255), nullable=True)
    image_size_bytes = Column(Integer, nullable=True)
    image_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0)
    author_user = relationship("User", foreign_keys=[author_user_id])

    __table_args__ = (
        Index("ix_community_chat_messages_room_created", "community_code", "created_at", "id"),
    )


class LocalGovernmentChatMembership(Base):
    __tablename__ = "lga_chat_memberships"

    id = Column(Integer, primary_key=True, index=True)
    lga_code = Column(String(16), ForeignKey("local_government_areas.code"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Integer, nullable=False, default=1, index=True)
    __table_args__ = (UniqueConstraint("lga_code", "user_id", name="uq_lga_chat_membership_user"),)


class LocalGovernmentChatMessage(Base):
    __tablename__ = "lga_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    lga_code = Column(String(16), ForeignKey("local_government_areas.code"), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    image_storage_key = Column(String(80), nullable=True)
    image_storage_backend = Column(String(16), nullable=True)
    image_content_type = Column(String(100), nullable=True)
    image_original_filename = Column(String(255), nullable=True)
    image_size_bytes = Column(Integer, nullable=True)
    image_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    is_deleted = Column(Integer, nullable=False, default=0)
    author_user = relationship("User", foreign_keys=[author_user_id])

    __table_args__ = (Index("ix_lga_chat_messages_room_created", "lga_code", "created_at", "id"),)
