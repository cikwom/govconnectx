import re
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.auth_security_event import AuthSecurityEvent
from app.models.password_reset_token import PasswordResetToken
from app.models.department import Department
from app.models.department_geographic_scope import DepartmentGeographicScope
from app.models.report import Report
from app.models.user import User
from app.routers.locations import seed_location_directory


class AuthenticationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
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
            db.query(AuthSecurityEvent).delete()\n            db.query(PasswordResetToken).delete()\n            db.query(DepartmentGeographicScope).delete()
            db.query(Report).delete()
            db.query(User).delete()
            db.commit()
        finally:
            db.close()

    def register(self, email):
        return self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Test Citizen", "password": "Strong-Test-Password-42"},
        )

    def login(self, email):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Strong-Test-Password-42"},
        )
        self.assertEqual(response.status_code, 200)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def test_password_reset_is_one_time_and_revokes_existing_sessions(self):
        self.assertEqual(self.register("recover@example.com").status_code, 201)
        old_headers = self.login("recover@example.com")

        with patch("app.routers.auth.send_notification_email") as send_email:
            response = self.client.post(
                "/api/v1/auth/password-reset/request",
                json={"email": "recover@example.com"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(send_email.call_count, 1)
            message = send_email.call_args.args[2]
            match = re.search(r"token=([A-Za-z0-9_-]+)", message)
            self.assertIsNotNone(match)
            reset_token = match.group(1)

        completed = self.client.post(
            "/api/v1/auth/password-reset/complete",
            json={"token": reset_token, "new_password": "New-Strong-Password-43"},
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=old_headers).status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/login",
                json={"email": "recover@example.com", "password": "Strong-Test-Password-42"},
            ).status_code,
            401,
        )
        new_login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "recover@example.com", "password": "New-Strong-Password-43"},
        )
        self.assertEqual(new_login.status_code, 200)

        reused = self.client.post(
            "/api/v1/auth/password-reset/complete",
            json={"token": reset_token, "new_password": "Another-Strong-Password-44"},
        )
        self.assertEqual(reused.status_code, 400)

    def test_password_reset_request_does_not_reveal_unknown_accounts(self):
        with patch("app.routers.auth.send_notification_email") as send_email:
            known = self.client.post("/api/v1/auth/password-reset/request", json={"email": "unknown@example.com"})
            self.assertEqual(known.status_code, 200)
            self.assertEqual(send_email.call_count, 0)
        self.assertIn("If an account matches", known.json()["message"])

    def test_successful_login_is_recorded_in_security_activity(self):
        self.assertEqual(self.register("activity@example.com").status_code, 201)
        headers = self.login("activity@example.com")
        response = self.client.get("/api/v1/auth/security/activity", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["event_type"], "login_success")

    def test_public_registration_always_creates_citizen(self):
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "citizen@example.com",
                "full_name": "Test Citizen",
                "password": "Strong-Test-Password-42",
                "role": "system_admin",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["role"], "citizen")

    def test_login_and_current_user_profile(self):
        self.assertEqual(self.register("person@example.com").status_code, 201)
        headers = self.login("person@example.com")
        response = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "person@example.com")
        self.assertEqual(response.json()["role"], "citizen")

    def test_reports_require_authentication(self):
        response = self.client.get("/api/v1/reports")
        self.assertEqual(response.status_code, 401)

    def test_citizens_only_see_their_own_reports(self):
        self.assertEqual(self.register("first@example.com").status_code, 201)
        first_headers = self.login("first@example.com")
        created = self.client.post(
            "/api/v1/reports",
            headers=first_headers,
            json={
                "title": "Broken streetlight",
                "description": "Streetlight is not working",
                "category": "Infrastructure",
                "latitude": 6.5244,
                "longitude": 3.3792,
            },
        )
        self.assertEqual(created.status_code, 201)
        report_id = created.json()["id"]

        self.assertEqual(self.register("second@example.com").status_code, 201)
        second_headers = self.login("second@example.com")
        listing = self.client.get("/api/v1/reports", headers=second_headers)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json(), [])
        hidden_report = self.client.get(f"/api/v1/reports/{report_id}", headers=second_headers)
        self.assertEqual(hidden_report.status_code, 404)

    def test_official_can_read_reports_across_citizens(self):
        self.assertEqual(self.register("reporter@example.com").status_code, 201)
        reporter_headers = self.login("reporter@example.com")
        created = self.client.post(
            "/api/v1/reports",
            headers=reporter_headers,
            json={
                "title": "Blocked drainage",
                "description": "Drainage is blocked",
                "category": "Environment",
                "latitude": 6.5244,
                "longitude": 3.3792,
                "incident_state_code": "NG025",
                "incident_lga_code": "NG025011",
            },
        )
        self.assertEqual(created.status_code, 201)

        db = self.TestSession()
        try:
            department = Department(name="Road Maintenance")
            db.add(department)
            db.flush()
            db.add(DepartmentGeographicScope(department_id=department.id, state_code="NG025"))
            official = User(
                email="official@example.com",
                full_name="Test Official",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="official",
                department_id=department.id,
                is_active=True,
            )
            db.add(official)
            db.flush()
            report = db.query(Report).first()
            report.department_id = department.id
            report.assigned_to_user_id = official.id
            db.commit()
        finally:
            db.close()

        official_headers = self.login("official@example.com")
        listing = self.client.get("/api/v1/reports", headers=official_headers)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)

    def test_citizen_cannot_assign_roles(self):
        self.assertEqual(self.register("citizen@example.com").status_code, 201)
        headers = self.login("citizen@example.com")
        response = self.client.patch(
            "/api/v1/auth/users/1/role",
            headers=headers,
            json={"role": "system_admin"},
        )
        self.assertEqual(response.status_code, 403)

    def test_system_admin_can_assign_roles(self):
        db = self.TestSession()
        try:
            db.add(User(
                email="root@example.com",
                full_name="Test Administrator",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="system_admin",
                is_active=True,
            ))
            db.commit()
        finally:
            db.close()

        self.assertEqual(self.register("official@example.com").status_code, 201)
        admin_headers = self.login("root@example.com")
        response = self.client.patch(
            "/api/v1/auth/users/2/role",
            headers=admin_headers,
            json={"role": "official"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "official")


if __name__ == "__main__":
    unittest.main()
