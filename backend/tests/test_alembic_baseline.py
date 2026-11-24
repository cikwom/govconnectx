import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy import Float, create_engine, inspect, text
from alembic.migration import MigrationContext
from alembic.operations import Operations

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base  # noqa: E402
from app.models import (  # noqa: E402,F401
    Community,
    CommunityMembership,
    CommunityPostAttachment,
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
from app.models.audit_event import AuditEvent  # noqa: E402,F401
from app.models.auth_security_event import AuthSecurityEvent  # noqa: E402,F401
from app.models.citizen_services import (  # noqa: E402,F401
    CommunityListing,
    PublicServiceDirectoryEntry,
    ReportEscalation,
    ReportFeedback,
)
from app.models.login_attempt import LoginAttempt  # noqa: E402,F401
from app.models.notification import Notification  # noqa: E402,F401
from app.models.notification_delivery import NotificationDelivery  # noqa: E402,F401
from app.models.password_reset_token import PasswordResetToken  # noqa: E402,F401
from app.models.phone_verification import PhoneVerification  # noqa: E402,F401
from app.models.staff_invitation import StaffInvitation  # noqa: E402,F401
from app.models.user_preference import UserPreference  # noqa: E402,F401


class AlembicBaselineTests(unittest.TestCase):
    def _config(self):
        config = Config(str(BACKEND_DIR / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
        return config

    def test_baseline_adopts_complete_schema_and_preserves_existing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            database_url = f"sqlite:///{Path(directory) / 'baseline.db'}"
            engine = create_engine(database_url)
            try:
                Base.metadata.create_all(bind=engine)
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "INSERT INTO users "
                            "(id, email, full_name, password_hash, role, token_version, "
                            "is_active, created_at) "
                            "VALUES (91, 'existing@example.test', 'Existing Citizen', "
                            "'not-a-real-password-hash', 'citizen', 0, 1, CURRENT_TIMESTAMP)"
                        )
                    )

                with patch.dict(
                    os.environ,
                    {"DATABASE_URL": database_url, "ENVIRONMENT": "test"},
                ):
                    command.upgrade(self._config(), "head")
                    with engine.connect() as connection:
                        revision = connection.execute(
                            text("SELECT version_num FROM alembic_version")
                        ).scalar_one()
                        existing_user = connection.execute(
                            text("SELECT email FROM users WHERE id = 91")
                        ).scalar_one()

                self.assertEqual(revision, "20261124_0003")
                self.assertEqual(existing_user, "existing@example.test")
            finally:
                engine.dispose()


    def test_phase_two_migration_allows_landmark_only_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            database_url = f"sqlite:///{Path(directory) / 'landmark-reports.db'}"
            engine = create_engine(database_url)
            try:
                Base.metadata.create_all(bind=engine)
                with engine.begin() as connection:
                    operations = Operations(MigrationContext.configure(connection))
                    with operations.batch_alter_table("reports", recreate="always") as batch:
                        batch.alter_column("latitude", existing_type=Float(), existing_nullable=True, nullable=False)
                        batch.alter_column("longitude", existing_type=Float(), existing_nullable=True, nullable=False)

                with patch.dict(
                    os.environ,
                    {"DATABASE_URL": database_url, "ENVIRONMENT": "test"},
                ):
                    command.upgrade(self._config(), "head")

                columns = {column["name"]: column for column in inspect(engine).get_columns("reports")}
                self.assertTrue(columns["latitude"]["nullable"])
                self.assertTrue(columns["longitude"]["nullable"])
            finally:
                engine.dispose()

    def test_baseline_refuses_incomplete_schema_without_stamping_it(self):
        with tempfile.TemporaryDirectory() as directory:
            database_url = f"sqlite:///{Path(directory) / 'incomplete.db'}"
            engine = create_engine(database_url)
            try:
                with engine.begin() as connection:
                    connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))

                with patch.dict(
                    os.environ,
                    {"DATABASE_URL": database_url, "ENVIRONMENT": "test"},
                ):
                    with self.assertRaisesRegex(RuntimeError, "not ready for Alembic baseline adoption"):
                        command.upgrade(self._config(), "head")

                self.assertIn("alembic_version", inspect(engine).get_table_names())
                with engine.connect() as connection:
                    recorded_revisions = connection.execute(
                        text("SELECT version_num FROM alembic_version")
                    ).all()
                self.assertEqual(recorded_revisions, [])
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
