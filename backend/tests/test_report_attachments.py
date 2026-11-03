import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.report import Report
from app.models.report_attachment import ReportAttachment
from app.models.user import User


class ReportAttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"REPORT_ATTACHMENT_DIR": self.temp_dir.name})
        self.env.start()
        db = self.Session()
        try:
            db.query(ReportAttachment).delete()
            db.query(Report).delete()
            db.query(User).delete()
            db.commit()
            self.owner = User(
                email="owner@example.com",
                full_name="Report Owner",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="citizen",
                is_active=True,
            )
            self.other = User(
                email="other@example.com",
                full_name="Other Citizen",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="citizen",
                is_active=True,
            )
            db.add_all([self.owner, self.other])
            db.flush()
            self.report = Report(
                title="Damaged road",
                description="Large pothole",
                category="Infrastructure",
                latitude=6.5,
                longitude=3.3,
                user_id=self.owner.id,
                status="SUBMITTED",
            )
            db.add(self.report)
            db.commit()
            self.report_id = self.report.id
        finally:
            db.close()
        self.owner_headers = self.login("owner@example.com")
        self.other_headers = self.login("other@example.com")

    def tearDown(self):
        self.env.stop()
        self.temp_dir.cleanup()

    def login(self, email):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Strong-Test-Password-42"},
        )
        self.assertEqual(response.status_code, 200)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def test_owner_can_upload_list_and_download_private_evidence(self):
        png = b"\x89PNG\r\n\x1a\n" + b"test-image-content"
        uploaded = self.client.post(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=self.owner_headers,
            files={"file": ("road-evidence.png", png, "image/png")},
        )
        self.assertEqual(uploaded.status_code, 201)
        metadata = uploaded.json()
        self.assertEqual(metadata["original_filename"], "road-evidence.png")
        self.assertEqual(metadata["size_bytes"], len(png))
        self.assertEqual(metadata["sha256"], hashlib.sha256(png).hexdigest())

        listing = self.client.get(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=self.owner_headers,
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)

        download = self.client.get(
            f"/api/v1/reports/{self.report_id}/attachments/{metadata['id']}/download",
            headers=self.owner_headers,
        )
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.content, png)
        self.assertEqual(download.headers["x-content-type-options"], "nosniff")

    def test_other_citizen_cannot_list_or_download_evidence(self):
        png = b"\x89PNG\r\n\x1a\n" + b"test-image-content"
        uploaded = self.client.post(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=self.owner_headers,
            files={"file": ("evidence.png", png, "image/png")},
        )
        attachment_id = uploaded.json()["id"]

        listing = self.client.get(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=self.other_headers,
        )
        self.assertEqual(listing.status_code, 404)
        download = self.client.get(
            f"/api/v1/reports/{self.report_id}/attachments/{attachment_id}/download",
            headers=self.other_headers,
        )
        self.assertEqual(download.status_code, 404)

    def test_rejects_invalid_file_content_and_mismatched_extension(self):
        invalid = self.client.post(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=self.owner_headers,
            files={"file": ("payload.png", b"not really a png", "image/png")},
        )
        self.assertEqual(invalid.status_code, 415)

        mismatch = self.client.post(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=self.owner_headers,
            files={"file": ("%2e%2e%2fsecret.pdf", b"\x89PNG\r\n\x1a\nimage", "image/png")},
        )
        self.assertEqual(mismatch.status_code, 415)


    def test_configured_upload_size_limit_is_enforced(self):
        png = b"\x89PNG\r\n\x1a\nX"
        with patch("app.routers.attachments.MAX_UPLOAD_BYTES", 8):
            response = self.client.post(
                f"/api/v1/reports/{self.report_id}/attachments",
                headers=self.owner_headers,
                files={"file": ("large.png", png, "image/png")},
            )
        self.assertEqual(response.status_code, 413)

    def test_assigned_department_official_can_access_report_evidence(self):
        db = self.Session()
        try:
            department = Department(name="Road Maintenance")
            db.add(department)
            db.flush()
            official = User(
                email="assigned-official@example.com",
                full_name="Assigned Official",
                password_hash=hash_password("Strong-Test-Password-42"),
                role="official",
                department_id=department.id,
                is_active=True,
            )
            db.add(official)
            db.flush()
            report = db.query(Report).filter(Report.id == self.report_id).one()
            report.department_id = department.id
            report.assigned_to_user_id = official.id
            db.commit()
        finally:
            db.close()

        official_headers = self.login("assigned-official@example.com")
        png = b"\x89PNG\r\n\x1a\n" + b"official-evidence"
        uploaded = self.client.post(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=official_headers,
            files={"file": ("inspection.png", png, "image/png")},
        )
        self.assertEqual(uploaded.status_code, 201)
        listing = self.client.get(
            f"/api/v1/reports/{self.report_id}/attachments",
            headers=official_headers,
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)


if __name__ == "__main__":
    unittest.main()
