from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.audit_event import record_audit_event
from app.models.community_discussion import CommunityPost, CommunityPostComment
from app.models.location import Community
from app.models.user import User

router = APIRouter(prefix="/api/v1/community-spaces", tags=["Community Connect"])
ANNOUNCEMENT_ROLES = {"official", "department_admin", "supervisor", "system_admin"}
MODERATOR_ROLES = {"department_admin", "supervisor", "system_admin"}


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
