from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)

    description = Column(Text, nullable=False)

    category = Column(String(100), nullable=False)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    address = Column(String(300), nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="SUBMITTED",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )