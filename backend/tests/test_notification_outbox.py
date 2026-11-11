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
from app.models.notification_delivery import NotificationDelivery
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.email_delivery import queue_notification_channels
from app.services.notification_outbox import deliver_notification_delivery, process_due_deliveries


class NotificationOutboxTests(unittest.TestCase):
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
            db.query(NotificationDelivery).delete()
            db.query(UserPreference).delete()
            db.query(User).delete()
            user = User(
                email="outbox@example.com",
                full_name="Outbox Test",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="citizen",
                is_active=True,
            )
            db.add(user)
            db.commit()
            self.user_id = user.id
        finally:
            db.close()

    def create_delivery(self, *, channel="email", attempts=0, max_attempts=5, status="queued", due=True):
        db = self.TestSession()
        try:
            delivery = NotificationDelivery(
                recipient_user_id=self.user_id,
                channel=channel,
                destination="outbox@example.com" if channel == "email" else "+2348012345678",
                subject="Report update" if channel == "email" else None,
                message="Sign in to review the update.",
                status=status,
                attempts=attempts,
                max_attempts=max_attempts,
                next_attempt_at=datetime.now(timezone.utc) - timedelta(seconds=1) if due else datetime.now(timezone.utc) + timedelta(minutes=5),
            )
            db.add(delivery)
            db.commit()
            return delivery.id
        finally:
            db.close()

    def test_successful_delivery_is_recorded(self):
        delivery_id = self.create_delivery()
        with patch("app.services.notification_outbox.SessionLocal", side_effect=lambda: self.TestSession()):
            with patch("app.services.notification_outbox.send_notification_email", return_value=True):
                self.assertTrue(deliver_notification_delivery(delivery_id))
        db = self.TestSession()
        try:
            row = db.get(NotificationDelivery, delivery_id)
            self.assertEqual(row.status, "sent")
            self.assertEqual(row.attempts, 1)
            self.assertIsNotNone(row.sent_at)
            self.assertIsNone(row.last_error)
        finally:
            db.close()

    def test_failed_delivery_is_scheduled_for_retry(self):
        delivery_id = self.create_delivery()
        with patch("app.services.notification_outbox.SessionLocal", side_effect=lambda: self.TestSession()):
            with patch("app.services.notification_outbox.send_notification_email", return_value=False):
                self.assertFalse(deliver_notification_delivery(delivery_id))
        db = self.TestSession()
        try:
            row = db.get(NotificationDelivery, delivery_id)
            self.assertEqual(row.status, "queued")
            self.assertEqual(row.attempts, 1)
            self.assertIsNotNone(row.next_attempt_at)
            self.assertEqual(row.last_error, "Provider delivery failed or is not configured")
        finally:
            db.close()

    def test_max_attempts_marks_delivery_failed(self):
        delivery_id = self.create_delivery(attempts=4, max_attempts=5)
        with patch("app.services.notification_outbox.SessionLocal", side_effect=lambda: self.TestSession()):
            with patch("app.services.notification_outbox.send_notification_email", return_value=False):
                self.assertFalse(deliver_notification_delivery(delivery_id))
        db = self.TestSession()
        try:
            row = db.get(NotificationDelivery, delivery_id)
            self.assertEqual(row.status, "failed")
            self.assertEqual(row.attempts, 5)
        finally:
            db.close()

    def test_worker_processes_due_retry_rows(self):
        delivery_id = self.create_delivery()
        with patch("app.services.notification_outbox.SessionLocal", side_effect=lambda: self.TestSession()):
            with patch("app.services.notification_outbox.send_notification_email", return_value=True):
                self.assertEqual(process_due_deliveries(batch_size=10), 1)
        db = self.TestSession()
        try:
            self.assertEqual(db.get(NotificationDelivery, delivery_id).status, "sent")
        finally:
            db.close()

    def test_queue_persists_only_opted_in_channels(self):
        db = self.TestSession()
        try:
            user = db.get(User, self.user_id)
            user.phone_number = "+2348012345678"
            user.phone_verified_at = datetime.now(timezone.utc)
            preference = UserPreference(
                user_id=user.id,
                email_notifications=False,
                sms_notifications=True,
                sms_consent_at=datetime.now(timezone.utc),
            )
            db.add(preference)
            tasks = BackgroundTasks()
            queue_notification_channels(db, tasks, user.id, "Report updated", "Private report title must not be in SMS.")
            rows = db.query(NotificationDelivery).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].channel, "sms")
            self.assertNotIn("Private report title", rows[0].message)
            self.assertEqual(len(tasks.tasks), 1)
        finally:
            db.close()

    def test_admin_delivery_endpoint_masks_destinations(self):
        db = self.TestSession()
        try:
            admin = User(
                email="outbox-admin@example.com",
                full_name="Outbox Admin",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="system_admin",
                is_active=True,
            )
            db.add(admin)
            db.flush()
            db.add(NotificationDelivery(
                recipient_user_id=admin.id,
                channel="sms",
                destination="+2348012345678",
                message="Private message",
                status="queued",
                next_attempt_at=datetime.now(timezone.utc),
            ))
            db.commit()
            headers = {"Authorization": "Bearer " + create_access_token(admin.id, admin.role)}
        finally:
            db.close()

        response = self.client.get("/api/v1/admin/notification-deliveries", headers=headers)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["queued"], 1)
        self.assertEqual(payload["items"][0]["destination"], "••••5678")
        self.assertNotIn("message", payload["items"][0])


if __name__ == "__main__":
    unittest.main()
