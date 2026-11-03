import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.report_attachment import ReportAttachment
from app.models.user import User
from app.routers.reports import get_accessible_report
from app.schemas.attachments import ReportAttachmentResponse

router = APIRouter(prefix="/api/v1/reports", tags=["Report evidence"])

MAX_UPLOAD_BYTES = max(1, int(os.getenv("REPORT_ATTACHMENT_MAX_BYTES", str(10 * 1024 * 1024))))
ALLOWED_TYPES = {
    "image/jpeg": (".jpg", ".jpeg"),
    "image/png": (".png",),
    "application/pdf": (".pdf",),
}


def storage_directory() -> Path:
    configured = os.getenv("REPORT_ATTACHMENT_DIR", "./private_uploads/report-evidence")
    path = Path(configured).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_original_filename(filename: str | None) -> str:
    name = Path(filename or "evidence").name
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return (name or "evidence")[:255]


def detect_content_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def attachment_path(storage_key: str) -> Path:
    # Storage keys are generated UUIDs, never client-supplied paths.
    if not re.fullmatch(r"[0-9a-f]{32}", storage_key):
        raise HTTPException(status_code=404, detail="Attachment not found")
    root = storage_directory()
    target = (root / storage_key).resolve()
    if target.parent != root:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return target


@router.post("/{report_id}/attachments", response_model=ReportAttachmentResponse, status_code=status.HTTP_201_CREATED)
def upload_report_attachment(
    report_id: int,
    file: Annotated[UploadFile, File(...)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = get_accessible_report(report_id, db, current_user)
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_BYTES}-byte upload limit")

    detected_type = detect_content_type(data)
    if detected_type is None or detected_type != file.content_type:
        raise HTTPException(status_code=415, detail="Only valid JPEG, PNG, and PDF evidence files are accepted")
    if Path(file.filename or "").suffix.lower() not in ALLOWED_TYPES[detected_type]:
        raise HTTPException(status_code=415, detail="File extension does not match its content")

    storage_key = uuid.uuid4().hex
    destination = attachment_path(storage_key)
    try:
        destination.write_bytes(data)
        attachment = ReportAttachment(
            report_id=report.id,
            uploaded_by_user_id=current_user.id,
            original_filename=safe_original_filename(file.filename),
            storage_key=storage_key,
            content_type=detected_type,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


@router.get("/{report_id}/attachments", response_model=list[ReportAttachmentResponse])
def list_report_attachments(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_report(report_id, db, current_user)
    return (
        db.query(ReportAttachment)
        .filter(ReportAttachment.report_id == report_id)
        .order_by(ReportAttachment.created_at.asc())
        .all()
    )


@router.get("/{report_id}/attachments/{attachment_id}/download")
def download_report_attachment(
    report_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_report(report_id, db, current_user)
    attachment = (
        db.query(ReportAttachment)
        .filter(ReportAttachment.id == attachment_id, ReportAttachment.report_id == report_id)
        .first()
    )
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = attachment_path(attachment.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file is unavailable")

    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=attachment.original_filename,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )
