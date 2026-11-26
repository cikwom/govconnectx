"""Add LGA-wide community chat rooms and member access.

Revision ID: 20261126_0006
Revises: 20261125_0005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261126_0006"
down_revision = "20261125_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "lga_chat_memberships" not in tables:
        op.create_table(
            "lga_chat_memberships",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lga_code", sa.String(length=16), sa.ForeignKey("local_government_areas.code"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("lga_code", "user_id", name="uq_lga_chat_membership_user"),
        )
        op.create_index("ix_lga_chat_memberships_lga_code", "lga_chat_memberships", ["lga_code"])
        op.create_index("ix_lga_chat_memberships_user_id", "lga_chat_memberships", ["user_id"])
        op.create_index("ix_lga_chat_memberships_is_active", "lga_chat_memberships", ["is_active"])
    if "lga_chat_messages" not in tables:
        op.create_table(
            "lga_chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lga_code", sa.String(length=16), sa.ForeignKey("local_government_areas.code"), nullable=False),
            sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("image_storage_key", sa.String(length=80), nullable=True),
            sa.Column("image_storage_backend", sa.String(length=16), nullable=True),
            sa.Column("image_content_type", sa.String(length=100), nullable=True),
            sa.Column("image_original_filename", sa.String(length=255), nullable=True),
            sa.Column("image_size_bytes", sa.Integer(), nullable=True),
            sa.Column("image_sha256", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index("ix_lga_chat_messages_lga_code", "lga_chat_messages", ["lga_code"])
        op.create_index("ix_lga_chat_messages_author_user_id", "lga_chat_messages", ["author_user_id"])
        op.create_index("ix_lga_chat_messages_created_at", "lga_chat_messages", ["created_at"])
        op.create_index("ix_lga_chat_messages_room_created", "lga_chat_messages", ["lga_code", "created_at", "id"])


def downgrade() -> None:
    op.drop_table("lga_chat_messages")
    op.drop_table("lga_chat_memberships")
