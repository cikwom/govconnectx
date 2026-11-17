import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.staff_invitation import StaffInvitation
from app.models.user import User


class StaffInvitationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_db():
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.client.close()
        cls.engine.dispose()

    def setUp(self):
        db = self.Session()
        try:
            db.query(StaffInvitation).delete()
            db.query(User).delete()
            db.query(Department).delete()
            db.add_all([
                User(email="staff-admin@example.com", full_name="System Admin", password_hash=hash_password("Test-Password-123"), role="system_admin", is_active=True),
                User(email="citizen@example.com", full_name="Citizen User", password_hash=hash_password("Test-Password-123"), role="citizen", is_active=True),
            ])
            db.add(Department(name="Public Works", is_active=True))
            db.commit()
            self.department_id = db.query(Department).filter(Department.name == "Public Works").one().id
        finally:
            db.close()

    def headers(self, email):
        response = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Test-Password-123"})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def test_admin_invites_staff_and_single_use_link_activates_account(self):
        response = self.client.post("/api/v1/admin/staff-invitations", headers=self.headers("staff-admin@example.com"), json={
            "email": "new-officer@example.com", "full_name": "New Field Officer",
            "role": "official", "department_id": self.department_id,
        })
        self.assertEqual(response.status_code, 201)
        invitation_url = response.json()["development_invitation_url"]
        token = invitation_url.split("token=", 1)[1]
        db = self.Session()
        try:
            invitation = db.query(StaffInvitation).one()
            self.assertNotIn(token, invitation.token_hash)
            self.assertEqual(invitation.role, "official")
        finally:
            db.close()

        accepted = self.client.post("/api/v1/staff-invitations/accept", json={"token": token, "password": "A-Strong-New-Password-123"})
        self.assertEqual(accepted.status_code, 200)
        replay = self.client.post("/api/v1/staff-invitations/accept", json={"token": token, "password": "Another-Strong-Password-123"})
        self.assertEqual(replay.status_code, 400)
        db = self.Session()
        try:
            user = db.query(User).filter(User.email == "new-officer@example.com").one()
            self.assertEqual(user.role, "official")
            self.assertEqual(user.department_id, self.department_id)
            self.assertTrue(user.is_active)
        finally:
            db.close()

    def test_non_admin_cannot_invite_and_citizen_email_cannot_be_promoted(self):
        payload = {"email": "someone@example.com", "full_name": "Someone New", "role": "supervisor"}
        denied = self.client.post("/api/v1/admin/staff-invitations", headers=self.headers("citizen@example.com"), json=payload)
        self.assertEqual(denied.status_code, 403)
        conflict = self.client.post("/api/v1/admin/staff-invitations", headers=self.headers("staff-admin@example.com"), json={
            **payload, "email": "citizen@example.com",
        })
        self.assertEqual(conflict.status_code, 409)

    def test_admin_can_revoke_invitation_and_public_acceptance_is_denied(self):
        created = self.client.post("/api/v1/admin/staff-invitations", headers=self.headers("staff-admin@example.com"), json={
            "email": "revoke-me@example.com", "full_name": "Revoke Me", "role": "department_admin",
        })
        invitation_id = created.json()["id"]
        token = created.json()["development_invitation_url"].split("token=", 1)[1]
        revoked = self.client.post(f"/api/v1/admin/staff-invitations/{invitation_id}/revoke", headers=self.headers("staff-admin@example.com"))
        self.assertEqual(revoked.status_code, 200)
        denied = self.client.post("/api/v1/staff-invitations/accept", json={"token": token, "password": "A-Strong-New-Password-123"})
        self.assertEqual(denied.status_code, 400)


if __name__ == "__main__":
    unittest.main()
