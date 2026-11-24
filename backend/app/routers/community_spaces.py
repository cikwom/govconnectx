from datetime import datetime, timezone
import hashlib
import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.community_discussion import CommunityPost, CommunityPostComment, CommunityPostImage
from app.models.location import Community
from app.models.user import User
from app.services.evidence_storage import StorageNotConfigured, delete_object, is_production_environment, read_object, s3_is_configured, scan_bytes, storage_is_production_ready, store_object

router = APIRouter(prefix="/api/v1/community-spaces", tags=["Community Connect"])
ANNOUNCEMENT_ROLES = {"official", "department_admin", "supervisor", "system_admin"}
MODERATOR_ROLES = {"department_admin", "supervisor", "system_admin"}
MAX_IMAGE_BYTES = max(1, int(os.getenv("COMMUNITY_IMAGE_MAX_BYTES", str(10 * 1024 * 1024))))


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


def _post_or_404(db: Session, post_id: int) -> CommunityPost:
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id, CommunityPost.is_hidden.is_(False)).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    return post


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
            "created_at": post.created_at,
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
    return {"id": post.id, "community_code": post.community_code, "author_user_id": actor.id,
            "author": actor, "body": post.body, "is_announcement": post.is_announcement,
            "created_at": post.created_at, "comment_count": 0}


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def list_post_comments(
    post_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    _post_or_404(db, post_id)
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
    _post_or_404(db, post_id)
    return db.query(CommunityPostImage).filter(
        CommunityPostImage.post_id == post_id
    ).order_by(CommunityPostImage.created_at.asc()).all()


@router.get("/posts/{post_id}/images/{image_id}")
def download_community_image(
    post_id: int, image_id: int,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    _post_or_404(db, post_id)
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
