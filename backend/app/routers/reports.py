from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])
STAFF_ROLES = ("official", "department_admin", "supervisor", "system_admin")

@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(report: ReportCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_report = Report(title=report.title, description=report.description, category=report.category, latitude=report.latitude, longitude=report.longitude, address=report.address, user_id=current_user.id)
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@router.get("", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Report)
    if current_user.role == "citizen":
        query = query.filter(Report.user_id == current_user.id)
    return query.order_by(Report.created_at.desc()).all()

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Report).filter(Report.id == report_id)
    if current_user.role == "citizen":
        query = query.filter(Report.user_id == current_user.id)
    report = query.first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report
