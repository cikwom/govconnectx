from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.report import Report
from app.models.report_assignment import ReportAssignment
from app.models.report_history import ReportStatusHistory
from app.models.user import User

router = APIRouter(prefix="/api/v1/admin", tags=["System administration"])


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    role_counts = dict(
        db.query(User.role, func.count(User.id)).group_by(User.role).all()
    )
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    status_counts = dict(
        db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
    )
    now = datetime.now(timezone.utc)
    overdue = (
        db.query(func.count(Report.id))
        .filter(
            Report.status.notin_(("RESOLVED", "REJECTED")),
            Report.sla_due_at.is_not(None),
            Report.sla_due_at < now,
        )
        .scalar()
        or 0
    )
    new_users_30d = (
        db.query(func.count(User.id))
        .filter(User.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0))
        .scalar()
        or 0
    )
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "by_role": role_counts,
            "registered_today": new_users_30d,
        },
        "reports": {
            "total": total_reports,
            "by_status": status_counts,
            "open": sum(count for status, count in status_counts.items() if status not in ("RESOLVED", "REJECTED")),
            "overdue": overdue,
        },
    }


@router.get("/users")
def list_users(
    search: str | None = Query(default=None, max_length=160),
    role: str | None = Query(default=None, max_length=30),
    active: bool | None = None,
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    query = db.query(User)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.full_name.ilike(term), User.email.ilike(term)))
    if role:
        query = query.filter(User.role == role)
    if active is not None:
        query = query.filter(User.is_active.is_(active))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "department_id": user.department_id,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "reports_submitted": db.query(func.count(Report.id)).filter(Report.user_id == user.id).scalar() or 0,
            }
            for user in users
        ],
    }


@router.get("/activity")
def get_activity(
    limit: int = Query(default=40, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    events = []
    history_rows = (
        db.query(ReportStatusHistory, User, Report)
        .join(User, User.id == ReportStatusHistory.changed_by_user_id)
        .join(Report, Report.id == ReportStatusHistory.report_id)
        .order_by(ReportStatusHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    for event, actor, report in history_rows:
        events.append({
            "id": f"status-{event.id}",
            "type": "report_status",
            "actor": actor.full_name,
            "actor_role": actor.role,
            "description": f'changed report #{report.id} from {event.old_status or "NEW"} to {event.new_status}',
            "report_id": report.id,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

    assignment_rows = (
        db.query(ReportAssignment, User, Report)
        .join(User, User.id == ReportAssignment.assigned_by_user_id)
        .join(Report, Report.id == ReportAssignment.report_id)
        .order_by(ReportAssignment.created_at.desc())
        .limit(limit)
        .all()
    )
    for event, actor, report in assignment_rows:
        events.append({
            "id": f"assignment-{event.id}",
            "type": "report_assignment",
            "actor": actor.full_name,
            "actor_role": actor.role,
            "description": f"assigned report #{report.id} to department #{event.department_id}",
            "report_id": report.id,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

    registration_rows = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .all()
    )
    for actor in registration_rows:
        events.append({
            "id": f"registration-{actor.id}",
            "type": "user_registered",
            "actor": actor.full_name,
            "actor_role": actor.role,
            "description": "created an account",
            "report_id": None,
            "created_at": actor.created_at.isoformat() if actor.created_at else None,
        })

    events.sort(key=lambda item: item["created_at"] or "", reverse=True)
    return events[:limit]
