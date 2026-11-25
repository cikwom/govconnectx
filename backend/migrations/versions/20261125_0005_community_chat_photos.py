"""Add private photo metadata to community chat messages.

Revision ID: 20261125_0005
Revises: 20261125_0004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261125_0005"
down_revision = "20261125_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("community_chat_messages")}
    additions = [
        ("image_storage_key", sa.String(length=80)),
        ("image_storage_backend", sa.String(length=16)),
        ("image_content_type", sa.String(length=100)),
        ("image_original_filename", sa.String(length=255)),
        ("image_size_bytes", sa.Integer()),
        ("image_sha256", sa.String(length=64)),
    ]
    for name, column_type in additions:
        if name not in columns:
            op.add_column("community_chat_messages", sa.Column(name, column_type, nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("community_chat_messages")}
    for name in ("image_sha256", "image_size_bytes", "image_original_filename", "image_content_type", "image_storage_backend", "image_storage_key"):
        if name in columns:
            op.drop_column("community_chat_messages", name)
