from sqlalchemy import Column, ForeignKey, String
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
