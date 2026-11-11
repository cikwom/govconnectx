import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config  # noqa: F401 - load .env before reading DATABASE_URL


def resolve_database_url(environment=None, database_url=None):
    """Resolve the database URL and reject ephemeral SQLite in production."""
    current_environment = (environment or os.getenv("ENVIRONMENT", "development")).strip().lower()
    configured_url = database_url or os.getenv("DATABASE_URL") or "sqlite:///./govconnect.db"
    configured_url = configured_url.strip()

    if current_environment == "production" and configured_url.lower().startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL must point to a managed production database; "
            "SQLite is only supported for local development and tests."
        )

    return configured_url


DATABASE_URL = resolve_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_existing_schema(database_engine=None):
    """Add nullable ownership, workflow, and geographical columns to existing databases."""
    target_engine = database_engine or engine
    inspector = inspect(target_engine)
    tables = set(inspector.get_table_names())
    with target_engine.begin() as connection:
        if "department_geographic_scopes" in tables:
            scope_columns = {column["name"] for column in inspector.get_columns("department_geographic_scopes")}
            if "ward_code" not in scope_columns:
                connection.execute(text("ALTER TABLE department_geographic_scopes ADD COLUMN ward_code VARCHAR(24) REFERENCES wards(code)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_department_geographic_scopes_ward_code ON department_geographic_scopes (ward_code)"))
        for table_name in ("wards", "communities"):
            if table_name in tables:
                columns = {column["name"] for column in inspector.get_columns(table_name)}
                additions = {
                    "source_name": "VARCHAR(180)",
                    "source_reference": "VARCHAR(500)",
                    "effective_from": "DATE",
                    "imported_at": "DATETIME",
                    "imported_by_user_id": "INTEGER REFERENCES users(id)",
                }
                for name, sql_type in additions.items():
                    if name not in columns:
                        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {sql_type}"))
        if "reports" in tables:
            columns = {column["name"] for column in inspector.get_columns("reports")}
            additions = {
                "user_id": "INTEGER REFERENCES users(id)",
                "department_id": "INTEGER REFERENCES departments(id)",
                "assigned_to_user_id": "INTEGER REFERENCES users(id)",
                "sla_due_at": "DATETIME",
                "resolved_at": "DATETIME",
                "incident_state_code": "VARCHAR(12)",
                "incident_lga_code": "VARCHAR(16)",
                "incident_ward_code": "VARCHAR(24)",
                "incident_community_code": "VARCHAR(32)",
                "gps_latitude": "FLOAT",
                "gps_longitude": "FLOAT",
                "location_review_status": "VARCHAR(24) NOT NULL DEFAULT 'not_provided'",
                "location_reviewed_by_user_id": "INTEGER REFERENCES users(id)",
                "location_reviewed_at": "DATETIME",
                "location_review_note": "TEXT",
            }
            for name, sql_type in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE reports ADD COLUMN {name} {sql_type}"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports (user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_department_id ON reports (department_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_assigned_to_user_id ON reports (assigned_to_user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_sla_due_at ON reports (sla_due_at)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_incident_state_code ON reports (incident_state_code)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_incident_lga_code ON reports (incident_lga_code)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_incident_ward_code ON reports (incident_ward_code)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_incident_community_code ON reports (incident_community_code)"))
        if "report_attachments" in tables:
            attachment_columns = {column["name"] for column in inspector.get_columns("report_attachments")}
            if "storage_backend" not in attachment_columns:
                connection.execute(text("ALTER TABLE report_attachments ADD COLUMN storage_backend VARCHAR(16) NOT NULL DEFAULT 'local'"))
        if "users" in tables:
            columns = {column["name"] for column in inspector.get_columns("users")}
            if "department_id" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN department_id INTEGER REFERENCES departments(id)"))
            if "home_state_code" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN home_state_code VARCHAR(12)"))
            if "home_lga_code" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN home_lga_code VARCHAR(16)"))
            if "phone_number" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)"))
            if "phone_verified_at" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN phone_verified_at DATETIME"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_number ON users (phone_number)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_department_id ON users (department_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_home_state_code ON users (home_state_code)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_home_lga_code ON users (home_lga_code)"))

        if "phone_verifications" in tables:
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_phone_verifications_created_at ON phone_verifications (created_at)"))
        if "user_preferences" in tables:
            columns = {column["name"] for column in inspector.get_columns("user_preferences")}
            additions = {
                "sms_notifications": "BOOLEAN NOT NULL DEFAULT 0",
                "sms_consent_at": "DATETIME",
                "sms_consent_revoked_at": "DATETIME",
            }
            for name, sql_type in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE user_preferences ADD COLUMN {name} {sql_type}"))
