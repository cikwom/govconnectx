from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database import Base, resolve_database_url

# Import every model module so all application tables are registered on Base.
from app.models import (  # noqa: F401
    Community,
    Department,
    DepartmentGeographicScope,
    DepartmentRoutingCategory,
    LocalGovernmentArea,
    Report,
    ReportAssignment,
    ReportAttachment,
    ReportComment,
    ReportStatusHistory,
    State,
    User,
    Ward,
)
from app.models.audit_event import AuditEvent  # noqa: F401
from app.models.auth_security_event import AuthSecurityEvent  # noqa: F401
from app.models.citizen_services import (  # noqa: F401
    CommunityListing,
    PublicServiceDirectoryEntry,
    ReportEscalation,
    ReportFeedback,
)
from app.models.login_attempt import LoginAttempt  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_delivery import NotificationDelivery  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.phone_verification import PhoneVerification  # noqa: F401
from app.models.staff_invitation import StaffInvitation  # noqa: F401
from app.models.user_preference import UserPreference  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = resolve_database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
