"""Create persistent community group chat messages.

Revision ID: 20261125_0004
Revises: 20261124_0003
"""
from alembic import op
import sqlalchemy as sa

revision = "20261125_0004"
down_revision = "20261124_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "community_chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("community_code", sa.String(length=32), sa.ForeignKey("communities.code"), nullable=False),
        sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_community_chat_messages_community_code", "community_chat_messages", ["community_code"])
    op.create_index("ix_community_chat_messages_author_user_id", "community_chat_messages", ["author_user_id"])
    op.create_index("ix_community_chat_messages_created_at", "community_chat_messages", ["created_at"])
    op.create_index("ix_community_chat_messages_room_created", "community_chat_messages", ["community_code", "created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_community_chat_messages_room_created", table_name="community_chat_messages")
    op.drop_index("ix_community_chat_messages_created_at", table_name="community_chat_messages")
    op.drop_index("ix_community_chat_messages_author_user_id", table_name="community_chat_messages")
    op.drop_index("ix_community_chat_messages_community_code", table_name="community_chat_messages")
    op.drop_table("community_chat_messages")
