import unittest
import os
import tempfile
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.location import Community, Ward
from app.models.user import User
from app.routers.locations import seed_location_directory


class CommunitySpaceApiTests(unittest.TestCase):
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
        self.community_code = "TEST-COMM-" + uuid4().hex[:12].upper()
        ward_code = "TEST-WARD-" + uuid4().hex[:10].upper()
        db = self.Session()
        seed_location_directory(db)
        db.add(Ward(code=ward_code, name="Test Community Ward", lga_code="NG025011", is_active=True))
        db.flush()
        db.add(Community(code=self.community_code, name="Test Community", ward_code=ward_code, is_active=True))
        db.commit()
        db.close()

    def create_user(self, role):
        email = f"{role}-{uuid4().hex}@example.com"
        db = self.Session()
        db.add(User(email=email, full_name=f"{role.title()} User", password_hash=hash_password("Strong-Test-Password-42"), role=role, is_active=True))
        db.commit()
        db.close()
        login = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Strong-Test-Password-42"})
        self.assertEqual(login.status_code, 200)
        return {"Authorization": "Bearer " + login.json()["access_token"]}

    def test_citizen_can_create_post_and_comment_in_selected_community(self):
        headers = self.create_user("citizen")
        created = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/posts",
            headers=headers, json={"body": "The streetlight near the market is not working."},
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["community_code"], self.community_code)
        self.assertEqual(created.json()["author"]["full_name"], "Citizen User")

        comment = self.client.post(
            f"/api/v1/community-spaces/posts/{created.json()['id']}/comments",
            headers=headers, json={"body": "I noticed this yesterday too."},
        )
        self.assertEqual(comment.status_code, 201)
        self.assertEqual(comment.json()["body"], "I noticed this yesterday too.")

        feed = self.client.get(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers)
        self.assertEqual(feed.status_code, 200)
        self.assertEqual(feed.json()[0]["comment_count"], 1)

    def test_citizen_cannot_publish_official_announcement(self):
        headers = self.create_user("citizen")
        response = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/posts",
            headers=headers, json={"body": "Official update", "is_announcement": True},
        )
        self.assertEqual(response.status_code, 403)

    def test_system_admin_can_publish_announcement_and_moderate_post(self):
        headers = self.create_user("system_admin")
        created = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/posts",
            headers=headers, json={"body": "Scheduled sanitation exercise", "is_announcement": True},
        )
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.json()["is_announcement"])
        hidden = self.client.patch(
            f"/api/v1/community-spaces/posts/{created.json()['id']}/moderation",
            headers=headers, json={"is_hidden": True},
        )
        self.assertEqual(hidden.status_code, 200)
        feed = self.client.get(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers)
        self.assertEqual(feed.json(), [])

    def test_unknown_community_is_not_created_implicitly(self):
        headers = self.create_user("citizen")
        response = self.client.get("/api/v1/community-spaces/UNKNOWN-COMMUNITY/posts", headers=headers)
        self.assertEqual(response.status_code, 404)


    def test_photo_upload_is_private_and_download_requires_authentication(self):
        headers = self.create_user("citizen")
        post = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/posts",
            headers=headers, json={"body": "Photo of the damaged streetlight."},
        )
        post_id = post.json()["id"]
        image_bytes = b"\xff\xd8\xff" + b"community-test-image"
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"COMMUNITY_MEDIA_DIR": directory}):
            uploaded = self.client.post(
                f"/api/v1/community-spaces/posts/{post_id}/images",
                headers=headers,
                files={"file": ("streetlight.jpg", image_bytes, "image/jpeg")},
            )
            self.assertEqual(uploaded.status_code, 201)
            image_id = uploaded.json()["id"]
            listing = self.client.get(f"/api/v1/community-spaces/posts/{post_id}/images", headers=headers)
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(listing.json()[0]["content_type"], "image/jpeg")
            download = self.client.get(f"/api/v1/community-spaces/posts/{post_id}/images/{image_id}", headers=headers)
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download.content, image_bytes)
            self.assertEqual(download.headers["cache-control"], "private, no-store")
            unauthenticated = self.client.get(f"/api/v1/community-spaces/posts/{post_id}/images/{image_id}")
            self.assertEqual(unauthenticated.status_code, 401)

    def test_discussion_endpoints_require_authentication(self):
        response = self.client.get(f"/api/v1/community-spaces/{self.community_code}/posts")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
