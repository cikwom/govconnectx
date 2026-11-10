from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


class State(Base):
    __tablename__ = "states"

    code = Column(String(12), primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(120), nullable=False, unique=True)
    geopolitical_zone = Column(String(30), nullable=False, index=True)
    local_governments = relationship("LocalGovernmentArea", back_populates="state")


class LocalGovernmentArea(Base):
    __tablename__ = "local_government_areas"

    code = Column(String(16), primary_key=True)
    name = Column(String(120), nullable=False, index=True)
    state_code = Column(String(12), ForeignKey("states.code"), nullable=False, index=True)
    state = relationship("State", back_populates="local_governments")



class Ward(Base):
    __tablename__ = "wards"

    code = Column(String(24), primary_key=True)
    name = Column(String(150), nullable=False, index=True)
    lga_code = Column(String(16), ForeignKey("local_government_areas.code"), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)


class Community(Base):
    __tablename__ = "communities"

    code = Column(String(32), primary_key=True)
    name = Column(String(180), nullable=False, index=True)
    ward_code = Column(String(24), ForeignKey("wards.code"), nullable=False, index=True)
    is_active = Column(__import__("sqlalchemy").Boolean, nullable=False, default=True)
