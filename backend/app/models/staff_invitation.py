from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class StaffInvitation(Base):
    __tablename__ = "staff_invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    role = Column(String(30), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    home_state_code = Column(String(12), ForeignKey("states.code"), nullable=True)
    home_lga_code = Column(String(16), ForeignKey("local_government_areas.code"), nullable=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
