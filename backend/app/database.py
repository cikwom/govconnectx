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
    """Add nullable ownership and workflow columns to pre-workflow databases."""
    target_engine = database_engine or engine
    inspector = inspect(target_engine)
    tables = set(inspector.get_table_names())
    with target_engine.begin() as connection:
        if "reports" in tables:
            columns = {column["name"] for column in inspector.get_columns("reports")}
            additions = {
                "user_id": "INTEGER REFERENCES users(id)",
                "department_id": "INTEGER REFERENCES departments(id)",
                "assigned_to_user_id": "INTEGER REFERENCES users(id)",
                "sla_due_at": "DATETIME",
                "resolved_at": "DATETIME",
            }
            for name, sql_type in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE reports ADD COLUMN {name} {sql_type}"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports (user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_department_id ON reports (department_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_assigned_to_user_id ON reports (assigned_to_user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_sla_due_at ON reports (sla_due_at)"))
        if "users" in tables:
            columns = {column["name"] for column in inspector.get_columns("users")}
            if "department_id" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN department_id INTEGER REFERENCES departments(id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_department_id ON users (department_id)"))
