from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from app.database import Base


class DepartmentGeographicScope(Base):
    """A department's authorized geographic coverage.

    A null LGA code means the whole state; a populated LGA code narrows
    coverage to that local government area.
    """
    __tablename__ = "department_geographic_scopes"
    __table_args__ = (
        UniqueConstraint("department_id", "state_code", "lga_code", name="uq_department_geographic_scope"),
    )

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    state_code = Column(String(12), ForeignKey("states.code"), nullable=False, index=True)
    lga_code = Column(String(16), ForeignKey("local_government_areas.code"), nullable=True, index=True)
