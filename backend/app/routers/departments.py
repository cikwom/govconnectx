from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.department import Department
from app.models.department_geographic_scope import DepartmentGeographicScope
from app.models.department_routing_category import DepartmentRoutingCategory
from app.models.location import LocalGovernmentArea, State
from app.models.user import User
from app.schemas.workflow import DepartmentCreate, DepartmentGeographicScopeInput, DepartmentGeographicScopeResponse, DepartmentMemberUpdate, DepartmentResponse, DepartmentRoutingCategoryInput, DepartmentRoutingCategoryResponse

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


@router.get("/{department_id}/geographic-scopes", response_model=list[DepartmentGeographicScopeResponse])
def list_department_geographic_scopes(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    department = db.query(Department).filter(Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return (
        db.query(DepartmentGeographicScope)
        .filter(DepartmentGeographicScope.department_id == department_id)
        .order_by(DepartmentGeographicScope.state_code, DepartmentGeographicScope.lga_code)
        .all()
    )


@router.put("/{department_id}/geographic-scopes", response_model=list[DepartmentGeographicScopeResponse])
def replace_department_geographic_scopes(
    department_id: int,
    scopes: list[DepartmentGeographicScopeInput],
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    """Replace a department's complete geographic jurisdiction.

    An empty list deliberately removes all jurisdiction and leaves the
    department unable to access geographically scoped reports.
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    normalized = set()
    validated = []
    for item in scopes:
        state_code = item.state_code.strip().upper()
        lga_code = item.lga_code.strip().upper() if item.lga_code else None
        key = (state_code, lga_code)
        if key in normalized:
            raise HTTPException(status_code=400, detail="Duplicate geographic scope")
        normalized.add(key)

        state = db.get(State, state_code)
        if state is None:
            raise HTTPException(status_code=400, detail=f"Unknown state code: {state_code}")
        if lga_code:
            lga = db.get(LocalGovernmentArea, lga_code)
            if lga is None or lga.state_code != state_code:
                raise HTTPException(status_code=400, detail="The selected LGA does not belong to the selected state")
        validated.append((state_code, lga_code))

    try:
        db.query(DepartmentGeographicScope).filter(
            DepartmentGeographicScope.department_id == department_id
        ).delete(synchronize_session=False)
        rows = [
            DepartmentGeographicScope(department_id=department_id, state_code=state_code, lga_code=lga_code)
            for state_code, lga_code in validated
        ]
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows
    except Exception:
        db.rollback()
        raise


@router.get("/{department_id}/routing-categories", response_model=list[DepartmentRoutingCategoryResponse])
def list_department_routing_categories(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    department = db.query(Department).filter(Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return db.query(DepartmentRoutingCategory).filter(
        DepartmentRoutingCategory.department_id == department_id
    ).order_by(DepartmentRoutingCategory.category).all()


@router.put("/{department_id}/routing-categories", response_model=list[DepartmentRoutingCategoryResponse])
def replace_department_routing_categories(
    department_id: int,
    categories: list[DepartmentRoutingCategoryInput],
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    """Replace the categories this department is eligible to receive."""
    department = db.query(Department).filter(Department.id == department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    normalized = {}
    for item in categories:
        category = " ".join(item.category.split())
        key = category.casefold()
        if key in normalized:
            raise HTTPException(status_code=400, detail="Duplicate routing category")
        normalized[key] = category

    try:
        db.query(DepartmentRoutingCategory).filter(
            DepartmentRoutingCategory.department_id == department_id
        ).delete(synchronize_session=False)
        rows = [
            DepartmentRoutingCategory(department_id=department_id, category=category)
            for category in normalized.values()
        ]
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows
    except Exception:
        db.rollback()
        raise
