import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.database import migrate_existing_schema


class LegacyDatabaseMigrationTests(unittest.TestCase):
    def test_legacy_schema_is_extended_without_losing_existing_reports(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
                connection.execute(text(
                    "CREATE TABLE reports (id INTEGER PRIMARY KEY, title VARCHAR(200) NOT NULL)"
                ))
                connection.execute(text(
                    "INSERT INTO reports (id, title) VALUES (41, 'Existing citizen report')"
                ))

            migrate_existing_schema(engine)
            migrate_existing_schema(engine)  # migration must be safe to rerun

            inspector = inspect(engine)
            report_columns = {column["name"] for column in inspector.get_columns("reports")}
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            report_indexes = {index["name"] for index in inspector.get_indexes("reports")}
            user_indexes = {index["name"] for index in inspector.get_indexes("users")}

            self.assertTrue(
                {"user_id", "department_id", "assigned_to_user_id"}.issubset(report_columns)
            )
            self.assertIn("department_id", user_columns)
            self.assertTrue({
                "ix_reports_user_id",
                "ix_reports_department_id",
                "ix_reports_assigned_to_user_id",
            }.issubset(report_indexes))
            self.assertIn("ix_users_department_id", user_indexes)

            with engine.connect() as connection:
                row = connection.execute(
                    text("SELECT id, title FROM reports WHERE id = 41")
                ).one()
            self.assertEqual((row.id, row.title), (41, "Existing citizen report"))
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
