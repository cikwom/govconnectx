from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.user import User

router = APIRouter(prefix="/api/v1/sla", tags=["Service levels"])
CLOSED = ("RESOLVED", "REJECTED")

@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Report).filter(Report.status.notin_(CLOSED))
    if user.role == "citizen":
        query = query.filter(Report.user_id == user.id)
    elif user.role == "official":
        query = query.filter(Report.department_id == user.department_id, Report.assigned_to_user_id == user.id)
    elif user.role in ("department_admin", "supervisor"):
        query = query.filter(Report.department_id == user.department_id)
    rows, now = query.all(), datetime.now(timezone.utc)
    deadlines = []
    for row in rows:
        value = row.sla_due_at
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        deadlines.append(value)
    return {
        "active_reports": len(rows),
        "overdue_reports": sum(1 for value in deadlines if value and value < now),
        "due_within_24_hours": sum(1 for value in deadlines if value and now <= value <= now + timedelta(hours=24)),
        "without_sla_deadline": sum(1 for value in deadlines if value is None),
    }
