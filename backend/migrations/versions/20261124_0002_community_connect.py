"""Create Community Connect discussion and media tables.

Revision ID: 20261124_0002
Revises: 20261123_0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261124_0002"
down_revision = "20261123_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "community_posts" not in tables:
        op.create_table(
            "community_posts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("community_code", sa.String(length=32), sa.ForeignKey("communities.code"), nullable=False),
            sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("is_announcement", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("moderated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if "community_post_comments" not in tables:
        op.create_table(
            "community_post_comments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("community_posts.id"), nullable=False),
            sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("moderated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if "community_post_images" not in tables:
        op.create_table(
            "community_post_images",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("community_posts.id"), nullable=False),
            sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("storage_key", sa.String(length=80), nullable=False, unique=True),
            sa.Column("storage_backend", sa.String(length=16), nullable=False, server_default="local"),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    tables = set(inspect(bind).get_table_names())
    indexes = {
        "community_posts": [
            ("ix_community_posts_id", ["id"], True),
            ("ix_community_posts_community_code", ["community_code"], False),
            ("ix_community_posts_author_user_id", ["author_user_id"], False),
            ("ix_community_posts_is_announcement", ["is_announcement"], False),
            ("ix_community_posts_is_hidden", ["is_hidden"], False),
            ("ix_community_posts_created_at", ["created_at"], False),
        ],
        "community_post_comments": [
            ("ix_community_post_comments_post_id", ["post_id"], False),
            ("ix_community_post_comments_author_user_id", ["author_user_id"], False),
            ("ix_community_post_comments_is_hidden", ["is_hidden"], False),
            ("ix_community_post_comments_created_at", ["created_at"], False),
        ],
        "community_post_images": [
            ("ix_community_post_images_post_id", ["post_id"], False),
            ("ix_community_post_images_uploaded_by_user_id", ["uploaded_by_user_id"], False),
            ("ix_community_post_images_storage_key", ["storage_key"], True),
            ("ix_community_post_images_created_at", ["created_at"], False),
        ],
    }
    for table_name, table_indexes in indexes.items():
        if table_name not in tables:
            continue
        existing = {item["name"] for item in inspect(bind).get_indexes(table_name)}
        for name, columns, unique in table_indexes:
            if name not in existing:
                op.create_index(name, table_name, columns, unique=unique)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    for table_name in ("community_post_images", "community_post_comments", "community_posts"):
        if table_name in tables:
            op.drop_table(table_name)
