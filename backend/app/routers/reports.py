from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.department import Department
from app.models.department_geographic_scope import DepartmentGeographicScope
from app.models.department_routing_category import DepartmentRoutingCategory
from app.models.report import Report
from app.models.location import LocalGovernmentArea, State
from app.models.report_assignment import ReportAssignment
from app.models.report_history import ReportComment, ReportStatusHistory
from app.models.notification import Notification
from app.models.audit_event import record_audit_event
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.schemas.workflow import AssignmentResponse, CommentCreate, CommentResponse, HistoryResponse, ReportAssignmentCreate, StatusUpdate

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])
STAFF_ROLES = ("official", "department_admin", "supervisor", "system_admin")
ALLOWED_TRANSITIONS = {
    "SUBMITTED": {"UNDER_REVIEW", "ASSIGNED", "REJECTED"},
    "UNDER_REVIEW": {"ASSIGNED", "REJECTED"},
    "ASSIGNED": {"IN_PROGRESS", "UNDER_REVIEW", "REJECTED"},
    "IN_PROGRESS": {"RESOLVED", "UNDER_REVIEW", "REJECTED"},
    "RESOLVED": {"UNDER_REVIEW"},
    "REJECTED": {"UNDER_REVIEW"},
}

def get_accessible_report(report_id: int, db: Session, user: User) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if user.role == "citizen":
        if report.user_id != user.id:
            raise HTTPException(status_code=404, detail="Report not found")
    elif user.role != "system_admin":
        if user.department_id is None or report.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="This report is outside your department")
        if not report.incident_state_code or not report.incident_lga_code:
            raise HTTPException(status_code=403, detail="This report has no verified geographic assignment")
        scope = db.query(DepartmentGeographicScope).filter(
            DepartmentGeographicScope.department_id == user.department_id,
            DepartmentGeographicScope.state_code == report.incident_state_code,
            (DepartmentGeographicScope.lga_code.is_(None) | (DepartmentGeographicScope.lga_code == report.incident_lga_code)),
        ).first()
        if scope is None:
            raise HTTPException(status_code=403, detail="This report is outside your department's geographic jurisdiction")
        if user.role == "official" and report.assigned_to_user_id != user.id:
            raise HTTPException(status_code=403, detail="This report is not assigned to you")
    return report

@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(report: ReportCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if bool(report.incident_state_code) != bool(report.incident_lga_code):
        raise HTTPException(status_code=400, detail="Select both the incident state and local government area")
    if report.incident_state_code:
        state = db.get(State, report.incident_state_code)
        lga = db.get(LocalGovernmentArea, report.incident_lga_code)
        if state is None or lga is None or lga.state_code != state.code:
            raise HTTPException(status_code=400, detail="The incident LGA does not belong to the selected state")
    sla_hours = max(1, int(os.getenv("REPORT_SLA_HOURS", "72")))
    routed_department = None
    if report.incident_state_code and report.incident_lga_code:
        candidates = (
            db.query(Department)
            .join(DepartmentRoutingCategory, DepartmentRoutingCategory.department_id == Department.id)
            .join(DepartmentGeographicScope, DepartmentGeographicScope.department_id == Department.id)
            .filter(
                Department.is_active.is_(True),
                func.lower(DepartmentRoutingCategory.category) == report.category.strip().lower(),
                DepartmentGeographicScope.state_code == report.incident_state_code,
                (DepartmentGeographicScope.lga_code.is_(None) | (DepartmentGeographicScope.lga_code == report.incident_lga_code)),
            )
            .distinct()
            .all()
        )
        # Only route automatically when exactly one active department matches.
        # Zero or multiple matches stay in the national administrator's triage queue.
        if len(candidates) == 1:
            routed_department = candidates[0]

    initial_status = "ASSIGNED" if routed_department else "SUBMITTED"
    new_report = Report(
        title=report.title,
        description=report.description,
        category=report.category,
        latitude=report.latitude,
        longitude=report.longitude,
        gps_latitude=report.gps_latitude,
        gps_longitude=report.gps_longitude,
        location_review_status="pending" if report.gps_latitude is not None and report.gps_longitude is not None else "not_provided",
        address=report.address,
        incident_state_code=report.incident_state_code,
        incident_lga_code=report.incident_lga_code,
        user_id=current_user.id,
        department_id=routed_department.id if routed_department else None,
        status=initial_status,
        sla_due_at=datetime.now(timezone.utc) + timedelta(hours=sla_hours),
    )
    db.add(new_report)
    db.flush()
    record_audit_event(db, actor_user_id=current_user.id, action="report.created", entity_type="report", entity_id=new_report.id, summary="Citizen submitted a community report", details={"category": new_report.category, "state_code": new_report.incident_state_code, "lga_code": new_report.incident_lga_code, "routed_department_id": new_report.department_id})
    history_message = (
        f"Automatically routed to {routed_department.name} using category and incident location"
        if routed_department else "Report submitted to the unassigned triage queue"
    )
    db.add(ReportStatusHistory(
        report_id=new_report.id,
        changed_by_user_id=current_user.id,
        old_status=None,
        new_status=initial_status,
        message=history_message,
        is_public=True,
    ))
    if routed_department:
        department_staff = db.query(User).filter(
            User.department_id == routed_department.id,
            User.is_active.is_(True),
            User.role.in_(("official", "department_admin", "supervisor")),
        ).all()
        for staff_member in department_staff:
            db.add(Notification(
                recipient_user_id=staff_member.id,
                report_id=new_report.id,
                event_type="report_auto_routed",
                title="New report routed to your department",
                message=f'Report "{new_report.title}" matches your department category and geographic coverage.',
            ))
    db.commit()
    db.refresh(new_report)
    return new_report

@router.get("", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Report)
    if current_user.role == "citizen":
        query = query.filter(Report.user_id == current_user.id)
    elif current_user.role == "system_admin":
        pass
    else:
        query = query.join(
            DepartmentGeographicScope,
            (DepartmentGeographicScope.department_id == Report.department_id)
            & (DepartmentGeographicScope.department_id == current_user.department_id)
            & (DepartmentGeographicScope.state_code == Report.incident_state_code)
            & (DepartmentGeographicScope.lga_code.is_(None) | (DepartmentGeographicScope.lga_code == Report.incident_lga_code)),
        )
        if current_user.role == "official":
            query = query.filter(Report.assigned_to_user_id == current_user.id)
        query = query.distinct()
    return query.order_by(Report.created_at.desc()).all()

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_accessible_report(report_id, db, current_user)

@router.post("/{report_id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_report(report_id: int, payload: ReportAssignmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("system_admin", "department_admin", "supervisor"))):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    department = db.query(Department).filter(Department.id == payload.department_id, Department.is_active.is_(True)).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Active department not found")
    if not report.incident_state_code or not report.incident_lga_code:
        raise HTTPException(status_code=400, detail="A report needs a verified State and LGA before geographic assignment")
    destination_scope = db.query(DepartmentGeographicScope).filter(
        DepartmentGeographicScope.department_id == payload.department_id,
        DepartmentGeographicScope.state_code == report.incident_state_code,
        (DepartmentGeographicScope.lga_code.is_(None) | (DepartmentGeographicScope.lga_code == report.incident_lga_code)),
    ).first()
    if destination_scope is None:
        raise HTTPException(status_code=400, detail="The selected department is not authorized for this report's geographic area")
    if current_user.role != "system_admin":
        if current_user.department_id != payload.department_id:
            raise HTTPException(status_code=403, detail="You can only assign reports to your own department")
        if report.department_id not in (None, current_user.department_id):
            raise HTTPException(status_code=403, detail="You cannot take a report from another department")
    if payload.assigned_to_user_id is not None:
        assignee = db.query(User).filter(User.id == payload.assigned_to_user_id, User.is_active.is_(True)).first()
        if assignee is None or assignee.role not in ("official", "department_admin", "supervisor") or assignee.department_id != payload.department_id:
            raise HTTPException(status_code=400, detail="Assignee must be active staff in the selected department")
    previous_status = report.status
    report.department_id = payload.department_id
    report.assigned_to_user_id = payload.assigned_to_user_id
    if report.status in ("SUBMITTED", "UNDER_REVIEW"):
        report.status = "ASSIGNED"
    assignment = ReportAssignment(report_id=report.id, department_id=payload.department_id, assigned_to_user_id=payload.assigned_to_user_id, assigned_by_user_id=current_user.id, note=payload.note)
    db.add(assignment)
    db.add(ReportStatusHistory(report_id=report.id, changed_by_user_id=current_user.id, old_status=previous_status, new_status=report.status, message=payload.note or "Report assigned", is_public=True))
    recipients = {report.user_id, report.assigned_to_user_id}
    recipients.discard(None)
    for recipient_id in recipients:
        db.add(Notification(recipient_user_id=recipient_id, report_id=report.id, event_type="report_assigned", title="Report assignment updated", message=f'Report "{report.title}" has been routed to {department.name}.'))
    record_audit_event(db, actor_user_id=current_user.id, action="report.assigned", entity_type="report", entity_id=report.id, summary="Report assigned to a department", details={"department_id": department.id, "assignee_user_id": payload.assigned_to_user_id})
    db.commit()
    db.refresh(assignment)
    return assignment

@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_report_status(report_id: int, payload: StatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*STAFF_ROLES))):
    report = get_accessible_report(report_id, db, current_user)
    new_status = payload.status.strip().upper()
    if new_status not in ALLOWED_TRANSITIONS.get(report.status, set()):
        raise HTTPException(status_code=400, detail=f"Status cannot change from {report.status} to {new_status}")
    old_status = report.status
    report.status = new_status
    if new_status == "RESOLVED":
        report.resolved_at = datetime.now(timezone.utc)
    elif old_status in ("RESOLVED", "REJECTED") and new_status == "UNDER_REVIEW":
        report.resolved_at = None
        sla_hours = max(1, int(os.getenv("REPORT_SLA_HOURS", "72")))
        report.sla_due_at = datetime.now(timezone.utc) + timedelta(hours=sla_hours)
    db.add(ReportStatusHistory(report_id=report.id, changed_by_user_id=current_user.id, old_status=old_status, new_status=new_status, message=payload.message, is_public=True))
    recipients = {report.user_id, report.assigned_to_user_id}
    recipients.discard(None)
    for recipient_id in recipients:
        if recipient_id != current_user.id:
            db.add(Notification(recipient_user_id=recipient_id, report_id=report.id, event_type="report_status_changed", title="Report status updated", message=f'Report "{report.title}" is now {new_status.replace("_", " ").lower()}.'))
    record_audit_event(db, actor_user_id=current_user.id, action="report.status_changed", entity_type="report", entity_id=report.id, summary="Report workflow status changed", details={"from": old_status, "to": new_status})
    db.commit()
    db.refresh(report)
    return report

@router.get("/{report_id}/history", response_model=list[HistoryResponse])
def get_report_history(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_accessible_report(report_id, db, current_user)
    query = db.query(ReportStatusHistory).filter(ReportStatusHistory.report_id == report_id)
    if current_user.role == "citizen":
        query = query.filter(ReportStatusHistory.is_public.is_(True))
    return query.order_by(ReportStatusHistory.created_at.asc()).all()

@router.get("/{report_id}/assignments", response_model=list[AssignmentResponse])
def get_report_assignments(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_accessible_report(report_id, db, current_user)
    if current_user.role == "citizen":
        raise HTTPException(status_code=403, detail="Assignment records are staff-only")
    return db.query(ReportAssignment).filter(ReportAssignment.report_id == report_id).order_by(ReportAssignment.created_at.asc()).all()

@router.post("/{report_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_report_comment(report_id: int, payload: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_accessible_report(report_id, db, current_user)
    if payload.is_internal and current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Internal notes are staff-only")
    comment = ReportComment(report_id=report_id, author_user_id=current_user.id, body=payload.body.strip(), is_internal=payload.is_internal)
    db.add(comment)
    record_audit_event(db, actor_user_id=current_user.id, action="report.comment_added", entity_type="report", entity_id=report_id, summary="A report comment was added", details={"internal": payload.is_internal})
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/{report_id}/comments", response_model=list[CommentResponse])
def get_report_comments(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_accessible_report(report_id, db, current_user)
    query = db.query(ReportComment).filter(ReportComment.report_id == report_id)
    if current_user.role == "citizen":
        query = query.filter(ReportComment.is_internal.is_(False))
    return query.order_by(ReportComment.created_at.asc()).all()
