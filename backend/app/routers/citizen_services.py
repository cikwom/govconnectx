from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.citizen_services import CommunityListing, PublicServiceDirectoryEntry, ReportEscalation, ReportFeedback
from app.models.location import LocalGovernmentArea, State
from app.models.notification import Notification
from app.models.report import Report
from app.models.user import User
from app.schemas.citizen_services import (
    EscalationCreate, EscalationReview, FeedbackCreate, FeedbackResponse,
    ListingCreate, ListingModeration, ListingResponse,
    ServiceDirectoryCreate, ServiceDirectoryResponse,
)
from app.routers.reports import get_accessible_report
from app.services.email_delivery import queue_notification_channels

router = APIRouter(prefix="/api/v1", tags=["Citizen services"])


def validate_location_pair(db: Session, state_code: str | None, lga_code: str | None):
    if bool(state_code) != bool(lga_code):
        raise HTTPException(status_code=400, detail="Select both state and LGA, or neither")
    if state_code:
        state = db.get(State, state_code.strip().upper())
        lga = db.get(LocalGovernmentArea, lga_code.strip().upper())
        if state is None or lga is None or lga.state_code != state.code:
            raise HTTPException(status_code=400, detail="The selected LGA does not belong to the selected state")


@router.get("/reports/{report_id}/duplicate-hint")
def duplicate_report_hint(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = get_accessible_report(report_id, db, current_user)
    report_created_at = report.created_at or datetime.now(timezone.utc)
    if report_created_at.tzinfo is None:
        report_created_at = report_created_at.replace(tzinfo=timezone.utc)
    since = report_created_at - timedelta(days=30)
    query = db.query(func.count(Report.id)).filter(
        Report.id != report.id,
        Report.category.ilike(report.category),
        Report.status.notin_(["RESOLVED", "REJECTED"]),
        Report.created_at >= since,
    )
    if report.incident_state_code and report.incident_lga_code:
        query = query.filter(
            Report.incident_state_code == report.incident_state_code,
            Report.incident_lga_code == report.incident_lga_code,
        )
    else:
        query = query.filter(Report.id == -1)
    count = query.scalar() or 0
    return {
        "possible_duplicate_count": count,
        "review_recommended": count > 0,
        "message": "Similar open reports may already exist in this area. Staff should review and link related cases; this is not an automatic rejection." if count else "No similar open reports were found in the same LGA during the previous 30 days.",
    }


@router.post("/reports/{report_id}/escalations", status_code=status.HTTP_201_CREATED)
def request_report_escalation(report_id: int, payload: EscalationCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = get_accessible_report(report_id, db, current_user)
    existing = db.query(ReportEscalation).filter(
        ReportEscalation.report_id == report.id,
        ReportEscalation.status == "PENDING",
        ReportEscalation.requested_by_user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have a pending escalation for this report")
    escalation = ReportEscalation(
        report_id=report.id,
        requested_by_user_id=current_user.id,
        urgency=payload.urgency,
        reason=payload.reason.strip(),
    )
    db.add(escalation)
    db.flush()
    record_audit_event(db, actor_user_id=current_user.id, action="report.escalation_requested", entity_type="report", entity_id=report.id, summary="A report was flagged for additional attention", details={"urgency": payload.urgency, "escalation_id": escalation.id})
    admins = db.query(User).filter(User.role == "system_admin", User.is_active.is_(True)).all()
    for admin in admins:
        db.add(Notification(
            recipient_user_id=admin.id,
            report_id=report.id,
            event_type="report_escalation_requested",
            title="Report requires escalation review",
            message=f"Report #{report.id} was flagged for {payload.urgency} attention. Review the report and escalation request.",
        ))
        queue_notification_channels(db, background_tasks, admin.id, "Report requires escalation review", f"Report #{report.id} was flagged for {payload.urgency} attention. Review the report and escalation request.")
    db.commit()
    db.refresh(escalation)
    return {"id": escalation.id, "report_id": report.id, "urgency": escalation.urgency, "status": escalation.status, "created_at": escalation.created_at.isoformat(), "notice": "This request alerts platform administrators; it is not an emergency dispatch service. If anyone is in immediate danger, contact the appropriate official emergency service directly."}


@router.patch("/admin/escalations/{escalation_id}")
def review_report_escalation(escalation_id: int, payload: EscalationReview, db: Session = Depends(get_db), current_user: User = Depends(require_roles("system_admin"))):
    escalation = db.query(ReportEscalation).filter(ReportEscalation.id == escalation_id).first()
    if escalation is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    escalation.status = payload.status
    escalation.reviewed_by_user_id = current_user.id
    escalation.reviewed_at = datetime.now(timezone.utc)
    record_audit_event(db, actor_user_id=current_user.id, action="report.escalation_reviewed", entity_type="report", entity_id=escalation.report_id, summary="Administrator reviewed a report escalation", details={"escalation_id": escalation.id, "status": payload.status})
    db.commit()
    return {"id": escalation.id, "report_id": escalation.report_id, "status": escalation.status, "reviewed_at": escalation.reviewed_at.isoformat()}


@router.post("/reports/{report_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_report_feedback(report_id: int, payload: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "RESOLVED":
        raise HTTPException(status_code=409, detail="Feedback is available after a report is marked resolved")
    if db.query(ReportFeedback).filter(ReportFeedback.report_id == report_id, ReportFeedback.citizen_user_id == current_user.id).first():
        raise HTTPException(status_code=409, detail="Feedback has already been submitted for this report")
    feedback = ReportFeedback(report_id=report_id, citizen_user_id=current_user.id, rating=payload.rating, comment=payload.comment.strip() if payload.comment else None)
    db.add(feedback)
    record_audit_event(db, actor_user_id=current_user.id, action="report.feedback_submitted", entity_type="report", entity_id=report_id, summary="Citizen submitted post-resolution feedback", details={"rating": payload.rating})
    db.commit()
    db.refresh(feedback)
    return feedback


@router.post("/community/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_community_listing(payload: ListingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    validate_location_pair(db, payload.state_code, payload.lga_code)
    listing = CommunityListing(
        listing_type=payload.listing_type,
        title=payload.title.strip(),
        description=payload.description.strip(),
        location_text=payload.location_text.strip(),
        state_code=payload.state_code.strip().upper() if payload.state_code else None,
        lga_code=payload.lga_code.strip().upper() if payload.lga_code else None,
        contact_instructions=payload.contact_instructions.strip(),
        created_by_user_id=current_user.id,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/community/listings", response_model=list[ListingResponse])
def list_community_listings(listing_type: str | None = Query(default=None, pattern="^(lost|found)$"), state_code: str | None = None, lga_code: str | None = None, limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(CommunityListing).filter(
        CommunityListing.moderation_status == "APPROVED",
        (CommunityListing.expires_at.is_(None) | (CommunityListing.expires_at > datetime.now(timezone.utc))),
    )
    if listing_type:
        query = query.filter(CommunityListing.listing_type == listing_type)
    if state_code:
        query = query.filter(CommunityListing.state_code == state_code.strip().upper())
    if lga_code:
        query = query.filter(CommunityListing.lga_code == lga_code.strip().upper())
    return query.order_by(CommunityListing.created_at.desc()).limit(limit).all()


@router.get("/admin/community/listings")
def list_pending_community_listings(
    moderation_status: str = Query(default="PENDING", pattern="^(PENDING|APPROVED|REJECTED)$"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    return (
        db.query(CommunityListing)
        .filter(CommunityListing.moderation_status == moderation_status)
        .order_by(CommunityListing.created_at.asc())
        .limit(limit)
        .all()
    )


@router.patch("/admin/community/listings/{listing_id}")
def moderate_community_listing(listing_id: int, payload: ListingModeration, db: Session = Depends(get_db), current_user: User = Depends(require_roles("system_admin"))):
    listing = db.query(CommunityListing).filter(CommunityListing.id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.moderation_status = payload.moderation_status
    record_audit_event(db, actor_user_id=current_user.id, action="community_listing.moderated", entity_type="community_listing", entity_id=listing.id, summary="Administrator moderated a Lost and Found listing", details={"status": payload.moderation_status})
    db.commit()
    return {"id": listing.id, "moderation_status": listing.moderation_status}


@router.post("/admin/service-directory", response_model=ServiceDirectoryResponse, status_code=status.HTTP_201_CREATED)
def create_service_directory_entry(payload: ServiceDirectoryCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("system_admin"))):
    validate_location_pair(db, payload.state_code, payload.lga_code)
    entry = PublicServiceDirectoryEntry(
        name=payload.name.strip(),
        category=payload.category.strip(),
        description=payload.description.strip(),
        address=payload.address.strip(),
        state_code=payload.state_code.strip().upper() if payload.state_code else None,
        lga_code=payload.lga_code.strip().upper() if payload.lga_code else None,
        phone=payload.phone.strip() if payload.phone else None,
        website=str(payload.website) if payload.website else None,
        is_verified=True,
        is_active=True,
        created_by_user_id=current_user.id,
    )
    db.add(entry)
    db.flush()
    record_audit_event(db, actor_user_id=current_user.id, action="service_directory.created", entity_type="service_directory_entry", entity_id=entry.id, summary="Administrator published a verified public service listing")
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/service-directory", response_model=list[ServiceDirectoryResponse])
def list_service_directory(category: str | None = None, state_code: str | None = None, lga_code: str | None = None, limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(PublicServiceDirectoryEntry).filter(
        PublicServiceDirectoryEntry.is_active.is_(True),
        PublicServiceDirectoryEntry.is_verified.is_(True),
    )
    if category:
        query = query.filter(PublicServiceDirectoryEntry.category.ilike(category.strip()))
    if state_code:
        query = query.filter(PublicServiceDirectoryEntry.state_code == state_code.strip().upper())
    if lga_code:
        query = query.filter(PublicServiceDirectoryEntry.lga_code == lga_code.strip().upper())
    return query.order_by(PublicServiceDirectoryEntry.name).limit(limit).all()
