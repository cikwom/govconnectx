"""Adopt the application-managed schema into Alembic version tracking.

Revision ID: 20261123_0001
Revises:
Create Date: 2026-11-23

This is deliberately a validation-only baseline. Existing installations use
SQLAlchemy create_all() and the legacy idempotent schema-extension routine.
This revision does not recreate or drop production tables. It records the
starting point only after the live schema matches registered application
metadata.
"""

from alembic import op
from sqlalchemy import inspect

from app.database import Base

# Import all model modules so metadata includes every mapped table.
from app.models import *  # noqa: F403,F401
from app.models.audit_event import AuditEvent  # noqa: F401
from app.models.auth_security_event import AuthSecurityEvent  # noqa: F401
from app.models.citizen_services import (
    CommunityListing,
    PublicServiceDirectoryEntry,
    ReportEscalation,
    ReportFeedback,
)  # noqa: F401
from app.models.login_attempt import LoginAttempt  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_delivery import NotificationDelivery  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.phone_verification import PhoneVerification  # noqa: F401
from app.models.staff_invitation import StaffInvitation  # noqa: F401
from app.models.user_preference import UserPreference  # noqa: F401

revision = "20261123_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    missing_tables = sorted(set(Base.metadata.tables) - existing_tables)
    missing_columns = []

    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        absent = sorted(set(table.columns.keys()) - existing_columns)
        if absent:
            missing_columns.append(f"{table_name}: {', '.join(absent)}")

    problems = []
    if missing_tables:
        problems.append("missing tables: " + ", ".join(missing_tables))
    if missing_columns:
        problems.append("missing columns: " + "; ".join(missing_columns))

    if problems:
        raise RuntimeError(
            "GovConnectX schema is not ready for Alembic baseline adoption ("
            + " | ".join(problems)
            + "). Start the application once with the configured DATABASE_URL "
            "so its existing schema bootstrap can run, then retry "
            "`alembic upgrade head`. Do not stamp or force this revision "
            "over an incomplete database."
        )


def downgrade() -> None:
    # The baseline owns no application tables. Downgrading only removes the
    # Alembic version marker; it intentionally preserves all application data.
    pass
