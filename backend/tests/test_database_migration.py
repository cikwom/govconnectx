import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.database import migrate_existing_schema


class LegacyDatabaseMigrationTests(unittest.TestCase):
    def test_legacy_reports_table_gets_owner_column_and_index(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
                connection.execute(text("CREATE TABLE reports (id INTEGER PRIMARY KEY, title VARCHAR(200) NOT NULL)"))

            migrate_existing_schema(engine)

            inspector = inspect(engine)
            columns = {column["name"] for column in inspector.get_columns("reports")}
            indexes = {index["name"] for index in inspector.get_indexes("reports")}
            self.assertIn("user_id", columns)
            self.assertIn("ix_reports_user_id", indexes)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
