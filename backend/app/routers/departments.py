from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.workflow import DepartmentCreate, DepartmentMemberUpdate, DepartmentResponse

router = APIRouter(prefix="/api/v1/departments", tags=["Departments"])

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("system_admin"))):
    name = " ".join(payload.name.split())
    if db.query(Department).filter(Department.name.ilike(name)).first():
        raise HTTPException(status_code=409, detail="Department already exists")
    department = Department(name=name, description=payload.description)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department

@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).filter(Department.is_active.is_(True)).order_by(Department.name).all()

@router.patch("/members/{user_id}", response_model=dict)
def set_user_department(user_id: int, payload: DepartmentMemberUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("system_admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role not in ("official", "department_admin", "supervisor"):
        raise HTTPException(status_code=400, detail="Only staff accounts can be assigned to a department")
    if payload.department_id is not None:
        department = db.query(Department).filter(Department.id == payload.department_id, Department.is_active.is_(True)).first()
        if department is None:
            raise HTTPException(status_code=404, detail="Active department not found")
    user.department_id = payload.department_id
    db.commit()
    return {"user_id": user.id, "department_id": user.department_id}
