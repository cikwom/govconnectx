import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.report import Report
from app.models.report_history import ReportStatusHistory
from app.models.report_assignment import ReportAssignment
from app.models.user import User


class AdminCommandCentreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.client.close()
        cls.engine.dispose()

    def setUp(self):
        db = self.TestSession()
        try:
            db.query(ReportStatusHistory).delete()
            db.query(ReportAssignment).delete()
            db.query(Report).delete()
            db.query(User).delete()
            db.add_all([
                User(email="admin@example.com", full_name="Platform Admin", password_hash=hash_password("Test-Password-123"), role="system_admin", is_active=True),
                User(email="citizen@example.com", full_name="A Citizen", password_hash=hash_password("Test-Password-123"), role="citizen", is_active=True),
            ])
            db.commit()
            citizen = db.query(User).filter(User.email == "citizen@example.com").one()
            report = Report(title="Broken streetlight", description="Streetlight is out on the main road", category="Infrastructure", latitude=6.5, longitude=3.3, address="Ikeja, Lagos", user_id=citizen.id, status="SUBMITTED")
            db.add(report)
            db.flush()
            db.add(ReportStatusHistory(report_id=report.id, changed_by_user_id=citizen.id, old_status=None, new_status="SUBMITTED", message="Report submitted", is_public=True))
            db.commit()
        finally:
            db.close()

    def headers(self, email):
        response = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Test-Password-123"})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def test_citizen_cannot_access_admin_overview(self):
        response = self.client.get("/api/v1/admin/overview", headers=self.headers("citizen@example.com"))
        self.assertEqual(response.status_code, 403)

    def test_admin_overview_counts_users_and_reports(self):
        response = self.client.get("/api/v1/admin/overview", headers=self.headers("admin@example.com"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["users"]["total"], 2)
        self.assertEqual(data["reports"]["total"], 1)
        self.assertEqual(data["reports"]["open"], 1)

    def test_admin_can_search_users_without_exposing_password_hash(self):
        response = self.client.get("/api/v1/admin/users?search=citizen", headers=self.headers("admin@example.com"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertNotIn("password_hash", response.json()["items"][0])

    def test_admin_can_see_reporter_and_report_content(self):
        response = self.client.get("/api/v1/admin/reports", headers=self.headers("admin@example.com"))
        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]
        self.assertEqual(item["title"], "Broken streetlight")
        self.assertEqual(item["reporter"]["email"], "citizen@example.com")

    def test_admin_activity_feed_contains_report_submission(self):
        response = self.client.get("/api/v1/admin/activity", headers=self.headers("admin@example.com"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("changed report #1 from NEW to SUBMITTED" in item["description"] for item in response.json()))


if __name__ == "__main__":
    unittest.main()
