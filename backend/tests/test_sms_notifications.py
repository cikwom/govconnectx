import re
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.background import BackgroundTasks

from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.phone_verification import PhoneVerification
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.sms_delivery import queue_notification_sms, send_sms


class SmsDeliveryServiceTests(unittest.TestCase):
    @patch.dict("os.environ", {"TERMII_API_KEY": "", "TERMII_SENDER_ID": ""})
    def test_sms_fails_closed_without_provider_configuration(self):
        self.assertFalse(send_sms("+2348012345678", "Test"))

    @patch("app.services.sms_delivery.httpx.post")
    @patch.dict("os.environ", {"TERMII_API_KEY": "test-key", "TERMII_SENDER_ID": "GovConnect"})
    def test_termii_adapter_sends_expected_payload(self, post):
        response = post.return_value
        response.json.return_value = {"code": "ok", "message_id": "test-message"}
        response.raise_for_status.return_value = None

        self.assertTrue(send_sms("+2348012345678", "Test message"))
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.ng.termii.com/api/sms/send")
        self.assertEqual(kwargs["json"]["to"], "+2348012345678")
        self.assertEqual(kwargs["json"]["sms"], "Test message")
        self.assertEqual(kwargs["json"]["api_key"], "test-key")


class PhoneVerificationApiTests(unittest.TestCase):
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
            db.query(PhoneVerification).delete()
            db.query(UserPreference).delete()
            db.query(User).delete()
            user = User(
                email="sms-citizen@example.com",
                full_name="SMS Citizen",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="citizen",
                is_active=True,
            )
            db.add(user)
            db.commit()
            self.user_id = user.id
            self.headers = {"Authorization": "Bearer " + create_access_token(user.id, user.role)}
        finally:
            db.close()

    def test_phone_must_be_verified_before_sms_opt_in(self):
        response = self.client.put(
            "/api/v1/preferences",
            headers=self.headers,
            json={
                "email_notifications": True,
                "in_app_notifications": True,
                "sms_notifications": True,
                "preferred_language": "en",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_verification_and_explicit_opt_in(self):
        captured = {}

        def fake_send(phone_number, message):
            captured["phone"] = phone_number
            captured["message"] = message
            return True

        with patch("app.routers.preferences.send_sms", side_effect=fake_send):
            requested = self.client.post(
                "/api/v1/preferences/phone/request-verification",
                headers=self.headers,
                json={"phone_number": "+2348012345678"},
            )
        self.assertEqual(requested.status_code, 200)
        code = re.search(r"([0-9]{6})", captured["message"]).group(1)

        verified = self.client.post(
            "/api/v1/preferences/phone/verify",
            headers=self.headers,
            json={"code": code},
        )
        self.assertEqual(verified.status_code, 200)
        self.assertIn("verified", verified.json()["message"].lower())

        opted_in = self.client.put(
            "/api/v1/preferences",
            headers=self.headers,
            json={
                "email_notifications": True,
                "in_app_notifications": True,
                "sms_notifications": True,
                "preferred_language": "en",
            },
        )
        self.assertEqual(opted_in.status_code, 200)
        self.assertTrue(opted_in.json()["sms_notifications"])
        self.assertIsNotNone(opted_in.json()["sms_consent_at"])
        self.assertEqual(opted_in.json()["phone_number"], "+2348012345678")

        opted_out = self.client.put(
            "/api/v1/preferences",
            headers=self.headers,
            json={
                "email_notifications": True,
                "in_app_notifications": True,
                "sms_notifications": False,
                "preferred_language": "en",
            },
        )
        self.assertEqual(opted_out.status_code, 200)
        self.assertFalse(opted_out.json()["sms_notifications"])
        self.assertIsNotNone(opted_out.json()["sms_consent_revoked_at"])

        reused = self.client.post(
            "/api/v1/preferences/phone/verify",
            headers=self.headers,
            json={"code": code},
        )
        self.assertEqual(reused.status_code, 400)

    def test_phone_number_rate_limit_applies_across_accounts(self):
        db = self.TestSession()
        try:
            now = datetime.now(timezone.utc)
            for _ in range(5):
                db.add(PhoneVerification(
                    user_id=self.user_id,
                    phone_number="+2348012345678",
                    code_hash="not-a-real-code-hash",
                    created_at=now - timedelta(minutes=2),
                    expires_at=now + timedelta(minutes=8),
                ))
            db.commit()
        finally:
            db.close()

        with patch("app.routers.preferences.send_sms") as send:
            response = self.client.post(
                "/api/v1/preferences/phone/request-verification",
                headers=self.headers,
                json={"phone_number": "+2348012345678"},
            )
        self.assertEqual(response.status_code, 429)
        send.assert_not_called()

    def test_phone_number_cannot_be_associated_with_another_account(self):
        db = self.TestSession()
        try:
            db.add(User(
                email="other-phone-owner@example.com",
                full_name="Other Owner",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="citizen",
                phone_number="+2348012345678",
                phone_verified_at=datetime.now(timezone.utc),
                is_active=True,
            ))
            db.commit()
        finally:
            db.close()

        with patch("app.routers.preferences.send_sms") as send:
            response = self.client.post(
                "/api/v1/preferences/phone/request-verification",
                headers=self.headers,
                json={"phone_number": "+2348012345678"},
            )
        self.assertEqual(response.status_code, 409)
        send.assert_not_called()

    def test_sms_notification_queue_requires_verified_number_and_consent(self):
        db = self.TestSession()
        try:
            user = db.get(User, self.user_id)
            user.phone_number = "+2348012345678"
            user.phone_verified_at = datetime.now(timezone.utc)
            preference = UserPreference(user_id=user.id, sms_notifications=False)
            db.add(preference)
            db.commit()

            tasks = BackgroundTasks()
            queue_notification_sms(db, tasks, user.id, "A report was updated")
            self.assertEqual(len(tasks.tasks), 0)

            preference.sms_notifications = True
            preference.sms_consent_at = datetime.now(timezone.utc)
            db.commit()
            queue_notification_sms(db, tasks, user.id, "A report was updated")
            self.assertEqual(len(tasks.tasks), 1)
        finally:
            db.close()

    def test_provider_failure_does_not_save_unverified_number(self):
        with patch("app.routers.preferences.send_sms", return_value=False):
            response = self.client.post(
                "/api/v1/preferences/phone/request-verification",
                headers=self.headers,
                json={"phone_number": "+2348012345678"},
            )
        self.assertEqual(response.status_code, 503)
        db = self.TestSession()
        try:
            user = db.get(User, self.user_id)
            self.assertIsNone(user.phone_number)
            self.assertEqual(db.query(PhoneVerification).count(), 0)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
