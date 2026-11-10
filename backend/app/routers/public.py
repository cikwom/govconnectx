from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.models.location import State
from app.models.report import Report

router = APIRouter(prefix="/api/v1/public", tags=["Public transparency"])


@router.get("/transparency")
def public_transparency_overview(db: Session = Depends(get_db)):
    """Publish aggregate service-accountability indicators without citizen or report details."""
    status_rows = db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
    status_counts = {status: count for status, count in status_rows}
    total = sum(status_counts.values())
    resolved = status_counts.get("RESOLVED", 0)
    open_count = sum(count for status, count in status_counts.items() if status not in ("RESOLVED", "REJECTED"))

    state_rows = (
        db.query(State.code, State.name, func.count(Report.id))
        .outerjoin(Report, Report.incident_state_code == State.code)
        .group_by(State.code, State.name)
        .order_by(State.name)
        .all()
    )
    # Suppress very small geographic counts in the public view to reduce re-identification risk.
    states = [
        {"state_code": code, "state_name": name, "reports": count if count >= 5 else None,
         "suppressed": 0 < count < 5}
        for code, name, count in state_rows
    ]

    category_rows = (
        db.query(Report.category, func.count(Report.id))
        .group_by(Report.category)
        .order_by(func.count(Report.id).desc())
        .all()
    )
    categories = [
        {"category": category, "reports": count}
        for category, count in category_rows
        if category and count >= 5
    ]

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "reports": {
            "total": total,
            "open": open_count,
            "resolved": resolved,
            "rejected": status_counts.get("REJECTED", 0),
            "resolution_rate_percent": round((resolved / total) * 100, 1) if total else 0,
        },
        "departments": {
            "active": db.query(func.count(Department.id)).filter(Department.is_active.is_(True)).scalar() or 0
        },
        "by_state": states,
        "by_category": categories,
        "privacy_note": "Only aggregate counts are public. Citizen identities, report descriptions, precise locations, comments and evidence are not included.",
    }
