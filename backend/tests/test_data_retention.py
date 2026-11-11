import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.notification_delivery import NotificationDelivery
from app.models.phone_verification import PhoneVerification
from app.models.user import User
from app.services.data_retention import prune_expired_phone_verifications, prune_notification_deliveries
from app.workers.notification_worker import wait_for_schema


class DataRetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        db = self.TestSession()
        try:
            db.query(NotificationDelivery).delete()
            db.query(PhoneVerification).delete()
            db.query(User).delete()
            user = User(
                email="retention@example.com",
                full_name="Retention Test",
                password_hash="not-used-in-this-test",
                role="citizen",
                is_active=True,
            )
            db.add(user)
            db.commit()
            self.user_id = user.id
        finally:
            db.close()

    def test_worker_schema_readiness_check_returns_when_tables_exist(self):
        wait_for_schema()

    def test_phone_verification_records_older_than_retention_are_deleted(self):
        now = datetime.now(timezone.utc)
        db = self.TestSession()
        try:
            db.add_all([
                PhoneVerification(
                    user_id=self.user_id,
                    phone_number="+2348012345678",
                    code_hash="old-hash",
                    created_at=now - timedelta(hours=25),
                    expires_at=now - timedelta(hours=24),
                ),
                PhoneVerification(
                    user_id=self.user_id,
                    phone_number="+2348012345678",
                    code_hash="recent-hash",
                    created_at=now - timedelta(hours=23),
                    expires_at=now - timedelta(hours=22),
                ),
            ])
            db.commit()
            self.assertEqual(prune_expired_phone_verifications(db, now=now, retention_hours=24), 1)
            db.commit()
            remaining = db.query(PhoneVerification).all()
            self.assertEqual(len(remaining), 1)
            self.assertEqual(remaining[0].code_hash, "recent-hash")
        finally:
            db.close()

    def test_notification_delivery_retention_is_disabled_without_explicit_policy(self):
        now = datetime.now(timezone.utc)
        db = self.TestSession()
        try:
            db.add(NotificationDelivery(
                recipient_user_id=self.user_id,
                channel="email",
                destination="retention@example.com",
                message="A report update is ready.",
                status="sent",
                created_at=now - timedelta(days=120),
                next_attempt_at=now - timedelta(days=120),
            ))
            db.commit()
            with patch.dict("os.environ", {"NOTIFICATION_DELIVERY_RETENTION_DAYS": "0"}):
                self.assertEqual(prune_notification_deliveries(db, now=now), 0)
            self.assertEqual(db.query(NotificationDelivery).count(), 1)
        finally:
            db.close()

    def test_notification_delivery_retention_deletes_only_old_terminal_rows(self):
        now = datetime.now(timezone.utc)
        db = self.TestSession()
        try:
            for status in ("sent", "failed", "queued", "sending"):
                db.add(NotificationDelivery(
                    recipient_user_id=self.user_id,
                    channel="email",
                    destination="retention@example.com",
                    message="A report update is ready.",
                    status=status,
                    created_at=now - timedelta(days=120),
                    next_attempt_at=now - timedelta(days=120),
                ))
            db.commit()
            self.assertEqual(prune_notification_deliveries(db, now=now, retention_days=90), 2)
            db.commit()
            remaining = {row.status for row in db.query(NotificationDelivery).all()}
            self.assertEqual(remaining, {"queued", "sending"})
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
