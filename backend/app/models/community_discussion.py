from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, index=True)
    community_code = Column(String(32), ForeignKey("communities.code"), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    is_announcement = Column(Boolean, nullable=False, default=False, index=True)
    is_hidden = Column(Boolean, nullable=False, default=False, index=True)
    moderated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    author_user = relationship("User", foreign_keys=[author_user_id])
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    author_user = relationship("User", foreign_keys=[author_user_id])


class CommunityPostComment(Base):
    __tablename__ = "community_post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False, index=True)
    moderated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
