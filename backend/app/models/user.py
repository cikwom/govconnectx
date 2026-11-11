from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="citizen", index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)\n    token_version = Column(Integer, nullable=False, default=0)
    home_state_code = Column(String(12), ForeignKey("states.code"), nullable=True, index=True)
    home_lga_code = Column(String(16), ForeignKey("local_government_areas.code"), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True, unique=True, index=True)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    reports = relationship("Report", back_populates="owner", foreign_keys="Report.user_id")
    department = relationship("Department", back_populates="users")
    home_state = relationship("State", foreign_keys=[home_state_code])
    home_lga = relationship("LocalGovernmentArea", foreign_keys=[home_lga_code])
