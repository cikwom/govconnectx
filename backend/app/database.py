import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config  # noqa: F401 - load .env before reading DATABASE_URL

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./govconnect.db")
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
    """Add the nullable report owner column and index to legacy databases."""
    target_engine = database_engine or engine
    inspector = inspect(target_engine)
    if "reports" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("reports")}
    with target_engine.begin() as connection:
        if "user_id" not in existing_columns:
            connection.execute(
                text("ALTER TABLE reports ADD COLUMN user_id INTEGER REFERENCES users(id)")
            )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports (user_id)")
        )
