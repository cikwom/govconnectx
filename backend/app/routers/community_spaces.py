from datetime import datetime, timezone
import asyncio
import hashlib
import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

import jwt

from app.core.dependencies import get_current_user
from app.core.security import decode_access_token
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.community_discussion import CommunityMembership, CommunityPost, CommunityPostAttachment, CommunityPostComment, CommunityPostImage
from app.models.location import Community, LocalGovernmentArea, State, Ward
from app.models.report_attachment import ReportAttachment
from app.schemas.report import ReportCreate
from app.models.user import User
from app.services.evidence_storage import StorageNotConfigured, delete_object, is_production_environment, read_object, s3_is_configured, scan_bytes, storage_is_production_ready, store_object

router = APIRouter(prefix="/api/v1/community-spaces", tags=["Community Connect"])

class CommunityLiveConnections:
    def __init__(self):
        self.connections: dict[str, list[tuple[WebSocket, asyncio.AbstractEventLoop]]] = {}

    async def connect(self, community_code: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(community_code, []).append((websocket, asyncio.get_running_loop()))

    def disconnect(self, community_code: str, websocket: WebSocket):
        remaining = [
            (connection, loop) for connection, loop in self.connections.get(community_code, [])
            if connection is not websocket
        ]
        if remaining:
            self.connections[community_code] = remaining
        else:
            self.connections.pop(community_code, None)

    async def _send(self, websocket: WebSocket, event: dict):
        try:
            await websocket.send_json(event)
        except Exception:
            # A closed client is removed when its receive loop exits.
            pass

    def broadcast_sync(self, community_code: str, event: dict):
        for websocket, loop in list(self.connections.get(community_code, [])):
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self._send(websocket, event), loop)


community_live_connections = CommunityLiveConnections()


@router.websocket("/{community_code}/live")
async def community_live_updates(
    websocket: WebSocket,
    community_code: str,
    db: Session = Depends(get_db),
):
    await websocket.accept()
    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = auth_message.get("token") if isinstance(auth_message, dict) and auth_message.get("type") == "authenticate" else None
        if not isinstance(token, str) or not token:
            await websocket.close(code=4401)
            return
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4401)
            return
        user_id = int(payload.get("sub", ""))
        actor = db.query(User).filter(User.id == user_id).first()
        if actor is None or not actor.is_active or payload.get("ver", 0) != actor.token_version:
            await websocket.close(code=4401)
            return
        community = _community_or_404(db, community_code)
        _require_membership(db, community.code, actor.id)
    except (jwt.InvalidTokenError, TypeError, ValueError):
        await websocket.close(code=4401)
        return
    except HTTPException as exc:
        await websocket.close(code=4403 if exc.status_code == 403 else 4404)
        return

    community_live_connections.connections.setdefault(community.code, []).append(
        (websocket, asyncio.get_running_loop())
    )
    try:
        await websocket.send_json({"type": "connected", "community_code": community.code})
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        community_live_connections.disconnect(community.code, websocket)

ANNOUNCEMENT_ROLES = {"official", "department_admin", "supervisor", "system_admin"}
MODERATOR_ROLES = {"department_admin", "supervisor", "system_admin"}
MAX_IMAGE_BYTES = max(1, int(os.getenv("COMMUNITY_IMAGE_MAX_BYTES", str(10 * 1024 * 1024))))
MAX_VIDEO_BYTES = max(1, int(os.getenv("COMMUNITY_VIDEO_MAX_BYTES", str(50 * 1024 * 1024))))


class PostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    is_announcement: bool = False


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ModerationUpdate(BaseModel):
    is_hidden: bool


class AuthorSummary(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class PostResponse(BaseModel):
    id: int
    community_code: str
    author_user_id: int
    author: AuthorSummary
    body: str
    is_announcement: bool
    created_at: datetime
    comment_count: int = 0
    converted_report_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_user_id: int
    author: AuthorSummary
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _community_or_404(db: Session, community_code: str) -> Community:
    community = db.query(Community).filter(Community.code == community_code.upper(), Community.is_active.is_(True)).first()
    if community is None:
        raise HTTPException(status_code=404, detail="Community not found or inactive")
    return community


def _membership_or_none(db: Session, community_code: str, user_id: int):
    return db.query(CommunityMembership).filter(
        CommunityMembership.community_code == community_code,
        CommunityMembership.user_id == user_id,
        CommunityMembership.is_active.is_(True),
    ).first()


def _require_membership(db: Session, community_code: str, user_id: int):
    if _membership_or_none(db, community_code, user_id) is None:
        raise HTTPException(status_code=403, detail="Join this community before posting, commenting, or sharing evidence")


def _post_or_404(db: Session, post_id: int) -> CommunityPost:
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id, CommunityPost.is_hidden.is_(False)).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    return post


@router.get("/{community_code}/membership")
def get_community_membership(
    community_code: str, db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    community = _community_or_404(db, community_code)
    membership = _membership_or_none(db, community.code, actor.id)
    return {"community_code": community.code, "is_member": membership is not None,
            "joined_at": membership.joined_at if membership else None}


@router.post("/{community_code}/membership", status_code=status.HTTP_200_OK)
def join_community(
    community_code: str, db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    community = _community_or_404(db, community_code)
    membership = db.query(CommunityMembership).filter(
        CommunityMembership.community_code == community.code,
        CommunityMembership.user_id == actor.id,
    ).first()
    if membership is None:
        membership = CommunityMembership(community_code=community.code, user_id=actor.id, is_active=True)
        db.add(membership)
    else:
        membership.is_active = True
        membership.joined_at = datetime.now(timezone.utc)
    record_audit_event(db, actor_user_id=actor.id, action="community.member_joined",
        entity_type="community", entity_id=None, summary="A citizen joined a community space",
        details={"community_code": community.code})
    db.commit()
    return {"community_code": community.code, "is_member": True, "joined_at": membership.joined_at}


@router.delete("/{community_code}/membership", status_code=status.HTTP_200_OK)
def leave_community(
    community_code: str, db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    community = _community_or_404(db, community_code)
    membership = _membership_or_none(db, community.code, actor.id)
    if membership is not None:
        membership.is_active = False
        record_audit_event(db, actor_user_id=actor.id, action="community.member_left",
            entity_type="community", entity_id=None, summary="A citizen left a community space",
            details={"community_code": community.code})
        db.commit()
    return {"community_code": community.code, "is_member": False}


@router.get("/{community_code}/posts", response_model=list[PostResponse])
def list_community_posts(
    community_code: str,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    community = _community_or_404(db, community_code)
    posts = (
        db.query(CommunityPost)
        .filter(CommunityPost.community_code == community.code, CommunityPost.is_hidden.is_(False))
        .order_by(CommunityPost.is_announcement.desc(), CommunityPost.created_at.desc(), CommunityPost.id.desc())
        .offset(offset).limit(limit).all()
    )
    result = []
    for post in posts:
        result.append({
            "id": post.id, "community_code": post.community_code, "author_user_id": post.author_user_id,
            "author": post.author_user, "body": post.body, "is_announcement": post.is_announcement,
            "created_at": post.created_at, "converted_report_id": post.converted_report_id,
            "comment_count": db.query(CommunityPostComment).filter(
                CommunityPostComment.post_id == post.id, CommunityPostComment.is_hidden.is_(False)
            ).count(),
        })
    return result


@router.post("/{community_code}/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_community_post(
    community_code: str,
    payload: PostCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    community = _community_or_404(db, community_code)
    _require_membership(db, community.code, actor.id)
    if payload.is_announcement and actor.role not in ANNOUNCEMENT_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised government staff can publish community announcements")
    post = CommunityPost(
        community_code=community.code, author_user_id=actor.id,
        body=payload.body.strip(), is_announcement=payload.is_announcement,
    )
    if not post.body:
        raise HTTPException(status_code=422, detail="Post text cannot be empty")
    db.add(post)
    db.flush()
    record_audit_event(
        db, actor_user_id=actor.id, action="community.post_created", entity_type="community_post",
        entity_id=post.id, summary="A community discussion post was created",
        details={"community_code": community.code, "announcement": post.is_announcement},
    )
    db.commit()
    db.refresh(post)
    community_live_connections.broadcast_sync(community.code, {"type": "post_created", "post_id": post.id})
    return {"id": post.id, "community_code": post.community_code, "author_user_id": actor.id,
            "author": actor, "body": post.body, "is_announcement": post.is_announcement,
            "created_at": post.created_at, "comment_count": 0, "converted_report_id": post.converted_report_id}


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def list_post_comments(
    post_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, _.id)
    comments = db.query(CommunityPostComment).filter(
        CommunityPostComment.post_id == post_id, CommunityPostComment.is_hidden.is_(False)
    ).order_by(CommunityPostComment.created_at.asc(), CommunityPostComment.id.asc()).all()
    return [{"id": item.id, "post_id": item.post_id, "author_user_id": item.author_user_id,
             "author": item.author_user, "body": item.body, "created_at": item.created_at} for item in comments]


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_post_comment(
    post_id: int, payload: CommentCreate,
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, actor.id)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Comment cannot be empty")
    comment = CommunityPostComment(post_id=post.id, author_user_id=actor.id, body=body)
    db.add(comment)
    db.flush()
    record_audit_event(
        db, actor_user_id=actor.id, action="community.comment_created", entity_type="community_post",
        entity_id=post.id, summary="A community discussion comment was created",
        details={"comment_id": comment.id, "community_code": post.community_code},
    )
    db.commit()
    db.refresh(comment)
    community_live_connections.broadcast_sync(post.community_code, {"type": "comment_created", "post_id": post.id, "comment_id": comment.id})
    return {"id": comment.id, "post_id": post.id, "author_user_id": actor.id,
            "author": actor, "body": comment.body, "created_at": comment.created_at}


@router.patch("/posts/{post_id}/moderation", status_code=status.HTTP_200_OK)
def moderate_community_post(
    post_id: int, payload: ModerationUpdate,
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    if actor.role not in MODERATOR_ROLES:
        raise HTTPException(status_code=403, detail="Community moderation permission required")
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    post.is_hidden = payload.is_hidden
    post.moderated_by_user_id = actor.id
    post.moderated_at = datetime.now(timezone.utc)
    record_audit_event(
        db, actor_user_id=actor.id, action="community.post_moderated", entity_type="community_post",
        entity_id=post.id, summary="A community post was moderated",
        details={"hidden": payload.is_hidden, "community_code": post.community_code},
    )
    db.commit()
    community_live_connections.broadcast_sync(post.community_code, {"type": "post_moderated", "post_id": post.id})
    return {"id": post.id, "is_hidden": post.is_hidden, "moderated_at": post.moderated_at}


class ImageResponse(BaseModel):
    id: int
    post_id: int
    uploaded_by_user_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _community_image_path(storage_key: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", storage_key):
        raise HTTPException(status_code=404, detail="Community image not found")
    root = Path(os.getenv("COMMUNITY_MEDIA_DIR", "./private_uploads/community-media")).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / storage_key).resolve()
    if target.parent != root:
        raise HTTPException(status_code=404, detail="Community image not found")
    return target


def _image_content_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


@router.post("/posts/{post_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
def upload_community_image(
    post_id: int, file: UploadFile = File(...),
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, actor.id)
    if is_production_environment() and not storage_is_production_ready():
        raise HTTPException(status_code=503, detail="Community image uploads require private durable storage and malware scanning.")
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The selected image is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the configured upload limit")
    detected = _image_content_type(data)
    declared = (file.content_type or "").lower().strip()
    suffix = Path(file.filename or "").suffix.lower()
    expected_suffix = {"image/jpeg": {".jpg", ".jpeg"}, "image/png": {".png"}}
    if detected is None or detected != declared or suffix not in expected_suffix[detected]:
        raise HTTPException(status_code=415, detail="Upload a valid JPEG or PNG image with a matching file type and extension")
    storage_key = uuid.uuid4().hex
    digest = hashlib.sha256(data).hexdigest()
    backend = "s3" if s3_is_configured() else "local"
    destination = _community_image_path(storage_key) if backend == "local" else None
    stored = False
    try:
        try:
            scan_bytes(data)
            if backend == "s3":
                store_object(storage_key, data, detected, digest)
            else:
                destination.write_bytes(data)
            stored = True
        except StorageNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        image = CommunityPostImage(
            post_id=post.id, uploaded_by_user_id=actor.id,
            original_filename=re.sub(r"[^A-Za-z0-9._ -]", "_", Path(file.filename or "image").name)[:255],
            storage_key=storage_key, storage_backend=backend, content_type=detected,
            size_bytes=len(data), sha256=digest,
        )
        db.add(image)
        db.flush()
        record_audit_event(
            db, actor_user_id=actor.id, action="community.image_uploaded", entity_type="community_post",
            entity_id=post.id, summary="A private image was attached to a community post",
            details={"image_id": image.id, "content_type": detected, "size_bytes": len(data), "storage_backend": backend},
        )
        db.commit()
        db.refresh(image)
        community_live_connections.broadcast_sync(post.community_code, {"type": "evidence_uploaded", "post_id": post.id})
        return image
    except Exception:
        db.rollback()
        if stored and backend == "s3":
            delete_object(storage_key)
        elif destination is not None:
            destination.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


@router.get("/posts/{post_id}/images", response_model=list[ImageResponse])
def list_community_images(
    post_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, _.id)
    return db.query(CommunityPostImage).filter(
        CommunityPostImage.post_id == post_id
    ).order_by(CommunityPostImage.created_at.asc()).all()


@router.get("/posts/{post_id}/images/{image_id}")
def download_community_image(
    post_id: int, image_id: int,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, _.id)
    image = db.query(CommunityPostImage).filter(
        CommunityPostImage.id == image_id, CommunityPostImage.post_id == post_id
    ).first()
    if image is None:
        raise HTTPException(status_code=404, detail="Community image not found")
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"}
    if image.storage_backend == "s3":
        try:
            obj = read_object(image.storage_key)
        except (StorageNotConfigured, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="Community image is unavailable") from exc
        return StreamingResponse(obj["Body"].iter_chunks(chunk_size=64 * 1024), media_type=image.content_type, headers=headers)
    path = _community_image_path(image.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Community image is unavailable")
    return FileResponse(path, media_type=image.content_type, filename=image.original_filename, headers=headers)


class CommunityReportConversion(BaseModel):
    title: str | None = Field(default=None, max_length=180)
    category: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=3, max_length=300)


@router.post("/posts/{post_id}/convert-to-report", status_code=status.HTTP_201_CREATED)
def convert_community_post_to_report(
    post_id: int, payload: CommunityReportConversion,
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    post = db.query(CommunityPost).filter(
        CommunityPost.id == post_id, CommunityPost.is_hidden.is_(False)
    ).with_for_update().first()
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    if post.author_user_id != actor.id:
        raise HTTPException(status_code=403, detail="Only the person who created this post can convert it into a report")
    _require_membership(db, post.community_code, actor.id)
    if post.converted_report_id is not None:
        raise HTTPException(status_code=409, detail="This community post has already been converted into a report")
    community = _community_or_404(db, post.community_code)
    ward = db.get(Ward, community.ward_code)
    lga = db.get(LocalGovernmentArea, ward.lga_code) if ward else None
    state = db.get(State, lga.state_code) if lga else None
    if ward is None or lga is None or state is None:
        raise HTTPException(status_code=409, detail="The community location directory is incomplete; an administrator must verify it before reporting")
    report_payload = ReportCreate(
        title=(payload.title or post.body.splitlines()[0][:180]).strip() or "Community-reported issue",
        description=f"{post.body.strip()}\n\nSubmitted from Community Connect post #{post.id}.",
        category=payload.category.strip(),
        latitude=None, longitude=None, address=payload.address.strip(),
        incident_state_code=state.code, incident_lga_code=lga.code,
        incident_ward_code=ward.code, incident_community_code=community.code,
    )
    from app.routers.reports import create_report
    report = create_report(report_payload, BackgroundTasks(), db, actor)

    # Carry community evidence into the official report's private evidence list.
    source_evidence = (
        db.query(CommunityPostImage).filter(CommunityPostImage.post_id == post.id).all()
        + db.query(CommunityPostAttachment).filter(CommunityPostAttachment.post_id == post.id).all()
    )
    report_evidence_count = 0
    report_media_root = Path(os.getenv("REPORT_ATTACHMENT_DIR", "./private_uploads/report-evidence")).expanduser().resolve()
    report_media_root.mkdir(parents=True, exist_ok=True)
    for item in source_evidence:
        if item.storage_backend == "local":
            source_path = _community_image_path(item.storage_key)
            if not source_path.is_file():
                continue
            destination = (report_media_root / item.storage_key).resolve()
            if destination.parent != report_media_root:
                continue
            destination.write_bytes(source_path.read_bytes())
        db.add(ReportAttachment(
            report_id=report.id, uploaded_by_user_id=item.uploaded_by_user_id,
            original_filename=item.original_filename, storage_key=item.storage_key,
            storage_backend=item.storage_backend, content_type=item.content_type,
            size_bytes=item.size_bytes, sha256=item.sha256,
        ))
        report_evidence_count += 1

    post.converted_report_id = report.id
    record_audit_event(
        db, actor_user_id=actor.id, action="community.post_converted_to_report",
        entity_type="community_post", entity_id=post.id,
        summary="A community discussion was submitted as an official report",
        details={"report_id": report.id, "community_code": community.code,
                 "evidence_count": report_evidence_count},
    )
    db.commit()
    community_live_connections.broadcast_sync(community.code, {"type": "post_converted_to_report", "post_id": post.id, "report_id": report.id})
    return {"report_id": report.id, "title": report.title, "status": report.status,
            "location": payload.address.strip(), "community_code": community.code}


class CommunityAttachmentResponse(BaseModel):
    id: int
    post_id: int
    uploaded_by_user_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _video_content_type(data: bytes) -> str | None:
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "video/quicktime" if data[8:12] == b"qt  " else "video/mp4"
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    return None


@router.post("/posts/{post_id}/attachments", response_model=CommunityAttachmentResponse, status_code=status.HTTP_201_CREATED)
def upload_community_video(
    post_id: int, file: UploadFile = File(...),
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, actor.id)
    if is_production_environment() and not storage_is_production_ready():
        raise HTTPException(status_code=503, detail="Community video uploads require private durable storage and malware scanning.")
    data = file.file.read(MAX_VIDEO_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The selected video is empty")
    if len(data) > MAX_VIDEO_BYTES:
        raise HTTPException(status_code=413, detail="Video exceeds the configured upload limit")
    detected = _video_content_type(data)
    declared = (file.content_type or "").lower().strip()
    suffixes = {"video/mp4": {".mp4", ".m4v"}, "video/quicktime": {".mov"}, "video/webm": {".webm"}}
    if detected is None or detected != declared or Path(file.filename or "").suffix.lower() not in suffixes[detected]:
        raise HTTPException(status_code=415, detail="Upload a valid MP4, WebM, or QuickTime video with a matching file type and extension")
    storage_key = uuid.uuid4().hex
    digest = hashlib.sha256(data).hexdigest()
    backend = "s3" if s3_is_configured() else "local"
    destination = _community_image_path(storage_key) if backend == "local" else None
    stored = False
    try:
        try:
            scan_bytes(data)
            if backend == "s3":
                store_object(storage_key, data, detected, digest)
            else:
                destination.write_bytes(data)
            stored = True
        except StorageNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        attachment = CommunityPostAttachment(
            post_id=post.id, uploaded_by_user_id=actor.id,
            original_filename=re.sub(r"[^A-Za-z0-9._ -]", "_", Path(file.filename or "video").name)[:255],
            storage_key=storage_key, storage_backend=backend, content_type=detected,
            size_bytes=len(data), sha256=digest,
        )
        db.add(attachment)
        db.flush()
        record_audit_event(
            db, actor_user_id=actor.id, action="community.video_uploaded",
            entity_type="community_post", entity_id=post.id,
            summary="A private video was attached to a community post",
            details={"attachment_id": attachment.id, "content_type": detected, "size_bytes": len(data)},
        )
        db.commit()
        db.refresh(attachment)
        community_live_connections.broadcast_sync(post.community_code, {"type": "evidence_uploaded", "post_id": post.id})
        return attachment
    except Exception:
        db.rollback()
        if stored and backend == "s3":
            delete_object(storage_key)
        elif destination is not None:
            destination.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


@router.get("/posts/{post_id}/attachments", response_model=list[CommunityAttachmentResponse])
def list_community_attachments(
    post_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, actor.id)
    return db.query(CommunityPostAttachment).filter(
        CommunityPostAttachment.post_id == post_id
    ).order_by(CommunityPostAttachment.created_at.asc()).all()


@router.get("/posts/{post_id}/attachments/{attachment_id}")
def download_community_attachment(
    post_id: int, attachment_id: int,
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    _require_membership(db, post.community_code, actor.id)
    attachment = db.query(CommunityPostAttachment).filter(
        CommunityPostAttachment.id == attachment_id, CommunityPostAttachment.post_id == post_id
    ).first()
    if attachment is None:
        raise HTTPException(status_code=404, detail="Community attachment not found")
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"}
    if attachment.storage_backend == "s3":
        try:
            obj = read_object(attachment.storage_key)
        except (StorageNotConfigured, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="Community attachment is unavailable") from exc
        return StreamingResponse(obj["Body"].iter_chunks(chunk_size=64 * 1024), media_type=attachment.content_type, headers=headers)
    path = _community_image_path(attachment.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Community attachment is unavailable")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_filename, headers=headers)
