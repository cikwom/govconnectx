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
                connection.execute(text("CREATE TABLE wards (code VARCHAR(24) PRIMARY KEY, name VARCHAR(150) NOT NULL, lga_code VARCHAR(16) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1)"))
                connection.execute(text("CREATE TABLE communities (code VARCHAR(32) PRIMARY KEY, name VARCHAR(180) NOT NULL, ward_code VARCHAR(24) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1)"))
                connection.execute(text(
                    "CREATE TABLE reports (id INTEGER PRIMARY KEY, title VARCHAR(200) NOT NULL)"
                ))
                connection.execute(text(
                    "CREATE TABLE department_geographic_scopes ("
                    "id INTEGER PRIMARY KEY, department_id INTEGER NOT NULL, "
                    "state_code VARCHAR(12) NOT NULL, lga_code VARCHAR(16))"
                ))
                connection.execute(text(
                    "INSERT INTO department_geographic_scopes "
                    "(id, department_id, state_code, lga_code) VALUES (7, 3, 'NG025', 'NG025011')"
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
            scope_columns = {column["name"] for column in inspector.get_columns("department_geographic_scopes")}
            ward_columns = {column["name"] for column in inspector.get_columns("wards")}
            community_columns = {column["name"] for column in inspector.get_columns("communities")}
            scope_indexes = {index["name"] for index in inspector.get_indexes("department_geographic_scopes")}

            provenance_columns = {"source_name", "source_reference", "effective_from", "imported_at", "imported_by_user_id"}
            self.assertTrue(provenance_columns.issubset(ward_columns))
            self.assertTrue(provenance_columns.issubset(community_columns))
            self.assertIn("ward_code", scope_columns)
            self.assertIn("ix_department_geographic_scopes_ward_code", scope_indexes)
            with engine.connect() as connection:
                scope = connection.execute(text(
                    "SELECT id, state_code, lga_code, ward_code "
                    "FROM department_geographic_scopes WHERE id = 7"
                )).one()
            self.assertEqual((scope.id, scope.state_code, scope.lga_code, scope.ward_code), (7, "NG025", "NG025011", None))

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
