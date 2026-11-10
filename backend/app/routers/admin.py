from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.report import Report
from app.models.location import LocalGovernmentArea, State
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


@router.get("/reports")
def list_all_reports(
    search: str | None = Query(default=None, max_length=160),
    status_filter: str | None = Query(default=None, alias="status", max_length=40),
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    query = db.query(Report, User).outerjoin(User, User.id == Report.user_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Report.title.ilike(term), Report.description.ilike(term), Report.category.ilike(term), Report.address.ilike(term), User.full_name.ilike(term), User.email.ilike(term)))
    if status_filter:
        query = query.filter(Report.status == status_filter.strip().upper())
    total = query.count()
    rows = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": report.id,
                "title": report.title,
                "description": report.description,
                "category": report.category,
                "status": report.status,
                "address": report.address,
                "department_id": report.department_id,
                "assigned_to_user_id": report.assigned_to_user_id,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "sla_due_at": report.sla_due_at.isoformat() if report.sla_due_at else None,
                "reporter": {"id": reporter.id, "full_name": reporter.full_name, "email": reporter.email} if reporter else None,
            }
            for report, reporter in rows
        ],
    }


@router.get("/oversight")
def get_reporting_oversight(
    window_days: int = Query(default=30, ge=1, le=365),
    min_reports: int = Query(default=5, ge=2, le=50),
    burst_threshold: int = Query(default=4, ge=2, le=20),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    """Return explainable reporting-pattern signals for human review.

    These signals identify unusual volume, short bursts and repeated content.
    They are not findings of fraud and must never trigger automatic penalties.
    """
    from collections import Counter, defaultdict
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=window_days)
    rows = (
        db.query(Report, User)
        .join(User, User.id == Report.user_id)
        .filter(User.role == "citizen", Report.created_at >= since)
        .order_by(User.id.asc(), Report.created_at.asc())
        .all()
    )

    grouped = defaultdict(list)
    for report, reporter in rows:
        grouped[reporter.id].append((report, reporter))

    candidates = []
    for user_rows in grouped.values():
        reporter = user_rows[0][1]
        reports = [item[0] for item in user_rows]
        timestamps = []
        for report in reports:
            created = report.created_at
            if created is None:
                continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            timestamps.append(created)
        timestamps.sort()

        max_24h = 0
        left = 0
        for right, timestamp in enumerate(timestamps):
            while timestamp - timestamps[left] > timedelta(hours=24):
                left += 1
            max_24h = max(max_24h, right - left + 1)

        fingerprints = Counter()
        for report in reports:
            title = " ".join((report.title or "").casefold().split())
            description = " ".join((report.description or "").casefold().split())
            category = " ".join((report.category or "").casefold().split())
            fingerprints[(category, title, description)] += 1
        repeated_content = sum(count - 1 for count in fingerprints.values() if count > 1)

        signals = []
        if len(reports) >= min_reports:
            signals.append({
                "code": "high_reporting_volume",
                "label": "High reporting volume",
                "detail": f"{len(reports)} reports submitted in {window_days} days (review threshold: {min_reports})",
            })
        if max_24h >= burst_threshold:
            signals.append({
                "code": "submission_burst",
                "label": "Submission burst",
                "detail": f"{max_24h} reports submitted within a 24-hour period (review threshold: {burst_threshold})",
            })
        if repeated_content:
            signals.append({
                "code": "repeated_report_content",
                "label": "Repeated report content",
                "detail": f"{repeated_content} report(s) repeat the same category, title and description",
            })
        if not signals:
            continue

        priority = "high" if len(signals) >= 2 else "medium"
        candidates.append({
            "user": {
                "id": reporter.id,
                "full_name": reporter.full_name,
                "email": reporter.email,
                "is_active": reporter.is_active,
            },
            "review_priority": priority,
            "reports_in_window": len(reports),
            "max_reports_in_24h": max_24h,
            "signals": signals,
            "reports": [
                {
                    "id": report.id,
                    "title": report.title,
                    "category": report.category,
                    "status": report.status,
                    "address": report.address,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                }
                for report in sorted(
                    reports,
                    key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True,
                )[:10]
            ],
        })

    candidates.sort(
        key=lambda item: (
            item["review_priority"] != "high",
            -len(item["signals"]),
            -item["reports_in_window"],
        )
    )
    selected = candidates[:limit]
    return {
        "window_days": window_days,
        "thresholds": {
            "min_reports": min_reports,
            "burst_threshold": burst_threshold,
            "burst_window_hours": 24,
        },
        "summary": {
            "citizens_reviewed": len(grouped),
            "flagged_citizens": len(candidates),
            "high_priority": sum(item["review_priority"] == "high" for item in candidates),
            "reports_analyzed": len(rows),
        },
        "items": selected,
        "notice": "These are review signals, not proof of false reporting. An administrator must examine the reports and evidence before taking action.",
    }


@router.get("/reports/unassigned")
def list_unassigned_reports(
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    """National triage queue for reports without one unambiguous department route."""
    query = db.query(Report).filter(Report.department_id.is_(None))
    total = query.count()
    rows = query.order_by(Report.created_at.asc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": report.id,
                "title": report.title,
                "description": report.description,
                "category": report.category,
                "status": report.status,
                "address": report.address,
                "incident_state_code": report.incident_state_code,
                "incident_lga_code": report.incident_lga_code,
                "created_at": report.created_at.isoformat() if report.created_at else None,
            }
            for report in rows
        ],
    }


@router.get("/geography/overview")
def get_geographic_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    """Return national -> geopolitical zone -> State -> LGA report totals."""
    report_rows = db.query(
        Report.incident_state_code,
        Report.incident_lga_code,
        Report.status,
        Report.department_id,
    ).all()
    state_counts = {}
    lga_counts = {}
    for state_code, lga_code, report_status, department_id in report_rows:
        if not state_code:
            continue
        state_bucket = state_counts.setdefault(state_code, {"total": 0, "open": 0, "unassigned": 0})
        state_bucket["total"] += 1
        if report_status not in ("RESOLVED", "REJECTED"):
            state_bucket["open"] += 1
        if department_id is None:
            state_bucket["unassigned"] += 1
        if lga_code:
            lga_bucket = lga_counts.setdefault(lga_code, {"total": 0, "open": 0, "unassigned": 0})
            lga_bucket["total"] += 1
            if report_status not in ("RESOLVED", "REJECTED"):
                lga_bucket["open"] += 1
            if department_id is None:
                lga_bucket["unassigned"] += 1

    zones = {}
    states = db.query(State).order_by(State.geopolitical_zone, State.name).all()
    lgas = db.query(LocalGovernmentArea).order_by(LocalGovernmentArea.name).all()
    lgas_by_state = {}
    for lga in lgas:
        lgas_by_state.setdefault(lga.state_code, []).append(lga)

    for state in states:
        zone = zones.setdefault(state.geopolitical_zone, {"name": state.geopolitical_zone, "total": 0, "open": 0, "unassigned": 0, "states": []})
        counts = state_counts.get(state.code, {"total": 0, "open": 0, "unassigned": 0})
        zone["total"] += counts["total"]
        zone["open"] += counts["open"]
        zone["unassigned"] += counts["unassigned"]
        zone["states"].append({
            "code": state.code,
            "name": state.name,
            **counts,
            "lgas": [
                {
                    "code": lga.code,
                    "name": lga.name,
                    **lga_counts.get(lga.code, {"total": 0, "open": 0, "unassigned": 0}),
                }
                for lga in lgas_by_state.get(state.code, [])
            ],
        })

    return {"country": "Nigeria", "total_states": len(states), "total_lgas": len(lgas), "geopolitical_zones": list(zones.values())}


@router.get("/reports/location-review")
def list_location_reviews(
    status_filter: str = Query(default="pending", alias="status", max_length=24),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    """List GPS-submitted reports for explicit national administrator review."""
    query = db.query(Report).filter(Report.gps_latitude.is_not(None), Report.gps_longitude.is_not(None))
    if status_filter != "all":
        query = query.filter(Report.location_review_status == status_filter)
    rows = query.order_by(Report.created_at.desc()).limit(limit).all()
    return {"items": [{
        "id": row.id, "title": row.title, "category": row.category,
        "gps_latitude": row.gps_latitude, "gps_longitude": row.gps_longitude,
        "incident_state_code": row.incident_state_code, "incident_lga_code": row.incident_lga_code,
        "address": row.address, "location_review_status": row.location_review_status,
        "location_reviewed_by_user_id": row.location_reviewed_by_user_id,
        "location_reviewed_at": row.location_reviewed_at.isoformat() if row.location_reviewed_at else None,
        "location_review_note": row.location_review_note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    } for row in rows]}


@router.patch("/reports/{report_id}/location-review")
def review_report_location(
    report_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("system_admin")),
):
    """Record an auditable human review; never overwrite the citizen's selected area."""
    from fastapi import HTTPException
    outcome = str(payload.get("status", "")).strip().lower()
    note = str(payload.get("note", "")).strip()
    if outcome not in ("verified", "mismatch", "unable_to_verify"):
        raise HTTPException(status_code=400, detail="Status must be verified, mismatch, or unable_to_verify")
    if len(note) > 1000:
        raise HTTPException(status_code=400, detail="Review note must be 1000 characters or fewer")
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.gps_latitude is None or report.gps_longitude is None:
        raise HTTPException(status_code=400, detail="This report has no citizen-shared GPS coordinates")
    report.location_review_status = outcome
    report.location_reviewed_by_user_id = reviewer.id
    report.location_reviewed_at = datetime.now(timezone.utc)
    report.location_review_note = note or None
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "location_review_status": report.location_review_status,
            "location_reviewed_by_user_id": report.location_reviewed_by_user_id,
            "location_reviewed_at": report.location_reviewed_at.isoformat(),
            "location_review_note": report.location_review_note,
            "incident_state_code": report.incident_state_code, "incident_lga_code": report.incident_lga_code}
