"""Add community membership, video attachments, report conversion and landmark-only reports.

Revision ID: 20261124_0003
Revises: 20261124_0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261124_0003"
down_revision = "20261124_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "community_posts" in tables:
        columns = {item["name"] for item in inspector.get_columns("community_posts")}
        if "converted_report_id" not in columns:
            with op.batch_alter_table("community_posts") as batch:
                batch.add_column(sa.Column("converted_report_id", sa.Integer(), nullable=True))
                batch.create_foreign_key(
                    "fk_community_posts_converted_report_id_reports",
                    "reports", ["converted_report_id"], ["id"],
                )
                batch.create_index("ix_community_posts_converted_report_id", ["converted_report_id"], unique=True)

    if "community_memberships" not in tables:
        op.create_table(
            "community_memberships",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("community_code", sa.String(32), sa.ForeignKey("communities.code"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("community_code", "user_id", name="uq_community_membership_user"),
        )
        op.create_index("ix_community_memberships_community_code", "community_memberships", ["community_code"])
        op.create_index("ix_community_memberships_user_id", "community_memberships", ["user_id"])
        op.create_index("ix_community_memberships_is_active", "community_memberships", ["is_active"])

    if "community_post_attachments" not in tables:
        op.create_table(
            "community_post_attachments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("community_posts.id"), nullable=False),
            sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("original_filename", sa.String(255), nullable=False),
            sa.Column("storage_key", sa.String(80), nullable=False, unique=True),
            sa.Column("storage_backend", sa.String(16), nullable=False, server_default="local"),
            sa.Column("content_type", sa.String(100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_community_post_attachments_post_id", "community_post_attachments", ["post_id"])
        op.create_index("ix_community_post_attachments_uploaded_by_user_id", "community_post_attachments", ["uploaded_by_user_id"])
        op.create_index("ix_community_post_attachments_storage_key", "community_post_attachments", ["storage_key"], unique=True)
        op.create_index("ix_community_post_attachments_created_at", "community_post_attachments", ["created_at"])

    if "reports" in tables:
        columns = {item["name"]: item for item in inspector.get_columns("reports")}
        if "latitude" in columns and columns["latitude"]["nullable"] is False:
            with op.batch_alter_table("reports") as batch:
                batch.alter_column("latitude", existing_type=sa.Float(), nullable=True)
                batch.alter_column("longitude", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "community_post_attachments" in tables:
        op.drop_table("community_post_attachments")
    if "community_memberships" in tables:
        op.drop_table("community_memberships")
    if "community_posts" in tables:
        columns = {item["name"] for item in inspect(bind).get_columns("community_posts")}
        if "converted_report_id" in columns:
            with op.batch_alter_table("community_posts") as batch:
                batch.drop_index("ix_community_posts_converted_report_id")
                batch.drop_constraint("fk_community_posts_converted_report_id_reports", type_="foreignkey")
                batch.drop_column("converted_report_id")
    # Coordinate columns intentionally remain nullable: reports created during
    # this revision may rely on verified community/landmark descriptions only.
