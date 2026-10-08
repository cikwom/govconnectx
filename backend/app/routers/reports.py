from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
)


@router.post("", response_model=ReportResponse)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
):
    new_report = Report(
        title=report.title,
        description=report.description,
        category=report.category,
        latitude=report.latitude,
        longitude=report.longitude,
        address=report.address,
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


@router.get("", response_model=list[ReportResponse])
def get_reports(
    db: Session = Depends(get_db),
):
    return db.query(Report).all()


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    return db.query(Report).filter(
        Report.id == report_id
    ).first()