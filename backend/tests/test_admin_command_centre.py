import unittest
from datetime import datetime, timezone

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
from app.routers.locations import seed_location_directory


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
            seed_location_directory(db)
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

    def test_citizen_cannot_access_reporting_oversight(self):
        response = self.client.get(
            "/api/v1/admin/oversight",
            headers=self.headers("citizen@example.com"),
        )
        self.assertEqual(response.status_code, 403)

    def test_oversight_flags_volume_burst_and_duplicate_content_for_review(self):
        db = self.TestSession()
        try:
            citizen = db.query(User).filter(User.email == "citizen@example.com").one()
            created_at = datetime.now(timezone.utc)
            db.add_all([
                Report(
                    title="Broken streetlight",
                    description="Streetlight is out on the main road",
                    category="Infrastructure",
                    latitude=6.5,
                    longitude=3.3,
                    address="Ikeja, Lagos",
                    incident_state_code="NG025",
                    incident_lga_code="NG025011",
                    user_id=citizen.id,
                    status="SUBMITTED",
                    created_at=created_at,
                ),
                Report(
                    title="Broken streetlight",
                    description="Streetlight is out on the main road",
                    category="Infrastructure",
                    latitude=6.5,
                    longitude=3.3,
                    address="Ikeja, Lagos",
                    user_id=citizen.id,
                    status="SUBMITTED",
                    created_at=created_at,
                ),
            ])
            db.commit()
        finally:
            db.close()

        response = self.client.get(
            "/api/v1/admin/oversight?window_days=30&min_reports=3&burst_threshold=3",
            headers=self.headers("admin@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["flagged_citizens"], 1)
        item = data["items"][0]
        self.assertEqual(item["user"]["email"], "citizen@example.com")
        self.assertEqual(item["review_priority"], "high")
        signal_codes = {signal["code"] for signal in item["signals"]}
        self.assertIn("high_reporting_volume", signal_codes)
        self.assertIn("submission_burst", signal_codes)
        self.assertIn("repeated_report_content", signal_codes)
        self.assertIn("not proof of false reporting", data["notice"])

    def test_admin_activity_feed_contains_report_submission(self):
        response = self.client.get("/api/v1/admin/activity", headers=self.headers("admin@example.com"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("changed report #1 from NEW to SUBMITTED" in item["description"] for item in response.json()))


    def test_admin_can_drill_down_from_geopolitical_zone_to_lga(self):
        response = self.client.get(
            "/api/v1/admin/geography/overview",
            headers=self.headers("admin@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["country"], "Nigeria")
        self.assertEqual(data["total_states"], 37)
        self.assertEqual(data["total_lgas"], 774)
        south_west = next(zone for zone in data["geopolitical_zones"] if zone["name"] == "South West")
        lagos = next(state for state in south_west["states"] if state["name"] == "Lagos")
        ikeja = next(lga for lga in lagos["lgas"] if lga["name"] == "Ikeja")
        self.assertEqual(lagos["total"], 1)
        self.assertEqual(ikeja["total"], 1)


if __name__ == "__main__":
    unittest.main()
