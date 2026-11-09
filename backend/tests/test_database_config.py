import unittest

from app.database import resolve_database_url


class DatabaseConfigurationTests(unittest.TestCase):
    def test_production_rejects_missing_database_url(self):
        with self.assertRaisesRegex(RuntimeError, "managed production database"):
            resolve_database_url(environment="production", database_url=None)

    def test_production_rejects_sqlite_database_url(self):
        with self.assertRaisesRegex(RuntimeError, "SQLite is only supported"):
            resolve_database_url(
                environment="production",
                database_url="sqlite:///./govconnect.db",
            )

    def test_production_accepts_managed_database_url(self):
        url = "postgresql+psycopg://user:password@db.example.test/govconnect"
        self.assertEqual(
            resolve_database_url(environment="production", database_url=url),
            url,
        )

    def test_development_keeps_sqlite_fallback(self):
        self.assertEqual(
            resolve_database_url(environment="development", database_url=None),
            "sqlite:///./govconnect.db",
        )

    def test_test_environment_allows_explicit_sqlite(self):
        self.assertEqual(
            resolve_database_url(
                environment="test",
                database_url="sqlite:///./test.db",
            ),
            "sqlite:///./test.db",
        )


if __name__ == "__main__":
    unittest.main()
