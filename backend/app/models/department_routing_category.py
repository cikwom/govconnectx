from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from app.database import Base


class DepartmentRoutingCategory(Base):
    """Incident categories a department is configured to receive automatically."""
    __tablename__ = "department_routing_categories"
    __table_args__ = (
        UniqueConstraint("department_id", "category", name="uq_department_routing_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
