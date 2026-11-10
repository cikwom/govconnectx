from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.database import Base


class ReportFeedback(Base):
    __tablename__ = "report_feedback"
    __table_args__ = (UniqueConstraint("report_id", "citizen_user_id", name="uq_report_feedback_citizen"),)

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    citizen_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReportEscalation(Base):
    __tablename__ = "report_escalations"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    urgency = Column(String(20), nullable=False, default="high")
    reason = Column(String(2000), nullable=False)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CommunityListing(Base):
    __tablename__ = "community_listings"

    id = Column(Integer, primary_key=True, index=True)
    listing_type = Column(String(20), nullable=False, index=True)  # lost or found
    title = Column(String(180), nullable=False)
    description = Column(String(3000), nullable=False)
    location_text = Column(String(300), nullable=False)
    state_code = Column(String(12), nullable=True, index=True)
    lga_code = Column(String(16), nullable=True, index=True)
    contact_instructions = Column(String(500), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    moderation_status = Column(String(20), nullable=False, default="PENDING", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)


class PublicServiceDirectoryEntry(Base):
    __tablename__ = "public_service_directory_entries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(180), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(String(2000), nullable=False)
    address = Column(String(400), nullable=False)
    state_code = Column(String(12), nullable=True, index=True)
    lga_code = Column(String(16), nullable=True, index=True)
    phone = Column(String(40), nullable=True)
    website = Column(String(300), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
