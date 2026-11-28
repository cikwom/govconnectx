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
from app.models.report import Report
from app.models.report_attachment import ReportAttachment
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

    def create_user(self, role, join=True):
        email = f"{role}-{uuid4().hex}@example.com"
        db = self.Session()
        db.add(User(email=email, full_name=f"{role.title()} User", password_hash=hash_password("Strong-Test-Password-42"), role=role, is_active=True))
        db.commit()
        db.close()
        login = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Strong-Test-Password-42"})
        self.assertEqual(login.status_code, 200)
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        if join:
            joined = self.client.post(f"/api/v1/community-spaces/{self.community_code}/membership", headers=headers)
            self.assertEqual(joined.status_code, 200)
        return headers


    def test_lga_chat_requires_membership_and_allows_joined_members_to_chat(self):
        headers = self.create_user("citizen", join=False)
        lga_code = "NG025011"
        endpoint = f"/api/v1/community-spaces/lgas/{lga_code}/chat"
        denied = self.client.get(endpoint + "/messages", headers=headers)
        self.assertEqual(denied.status_code, 403)
        joined = self.client.post(endpoint + "/membership", headers=headers)
        self.assertEqual(joined.status_code, 200)
        self.assertEqual(joined.json()["room_code"], "LGA-" + lga_code)
        sent = self.client.post(endpoint + "/messages", headers=headers, json={"body": "Good morning, Otukpo."})
        self.assertEqual(sent.status_code, 201, sent.text)
        self.assertEqual(sent.json()["community_code"], "LGA-" + lga_code)
        history = self.client.get(endpoint + "/messages", headers=headers)
        self.assertEqual(history.status_code, 200)
        self.assertIn("Good morning, Otukpo.", [item["body"] for item in history.json()])
        left = self.client.delete(endpoint + "/membership", headers=headers)
        self.assertFalse(left.json()["is_member"])
        denied_again = self.client.get(endpoint + "/messages", headers=headers)
        self.assertEqual(denied_again.status_code, 403)

    def test_lga_chat_photo_is_member_only_and_private(self):
        headers = self.create_user("citizen", join=False)
        other_headers = self.create_user("citizen", join=False)
        lga_code = "NG025011"
        endpoint = f"/api/v1/community-spaces/lgas/{lga_code}/chat"
        self.client.post(endpoint + "/membership", headers=headers)
        image_bytes = b"\xff\xd8\xff" + b"lga-chat-test-image"
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"COMMUNITY_MEDIA_DIR": directory}):
            uploaded = self.client.post(endpoint + "/messages/image", headers=headers,
                files={"file": ("otukpo.jpg", image_bytes, "image/jpeg")}, data={"body": "Road damage near the market."})
            self.assertEqual(uploaded.status_code, 201, uploaded.text)
            message_id = uploaded.json()["id"]
            download = self.client.get(endpoint + f"/messages/{message_id}/image", headers=headers)
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download.content, image_bytes)
            self.assertEqual(download.headers["cache-control"], "private, no-store")
            forbidden = self.client.get(endpoint + f"/messages/{message_id}/image", headers=other_headers)
            self.assertEqual(forbidden.status_code, 403)

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


    def test_membership_is_required_to_post_and_can_be_revoked(self):
        headers = self.create_user("citizen", join=False)
        denied = self.client.post(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers, json={"body": "Not a member yet"})
        self.assertEqual(denied.status_code, 403)
        joined = self.client.post(f"/api/v1/community-spaces/{self.community_code}/membership", headers=headers)
        self.assertEqual(joined.status_code, 200)
        created = self.client.post(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers, json={"body": "Now I am a member"})
        self.assertEqual(created.status_code, 201)
        left = self.client.delete(f"/api/v1/community-spaces/{self.community_code}/membership", headers=headers)
        self.assertFalse(left.json()["is_member"])
        denied_again = self.client.post(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers, json={"body": "I have left"})
        self.assertEqual(denied_again.status_code, 403)

    def test_post_author_can_convert_discussion_to_landmark_report_without_gps(self):
        headers = self.create_user("citizen")
        created = self.client.post(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers, json={"body": "A large drainage blockage is flooding the market road."})
        response = self.client.post(
            f"/api/v1/community-spaces/posts/{created.json()['id']}/convert-to-report",
            headers=headers, json={"category": "Infrastructure", "address": "Beside the community market entrance"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        db = self.Session()
        report = db.get(Report, response.json()["report_id"])
        self.assertIsNone(report.latitude)
        self.assertIsNone(report.longitude)
        self.assertEqual(report.address, "Beside the community market entrance")
        self.assertEqual(report.incident_community_code, self.community_code)
        db.close()
        duplicate = self.client.post(
            f"/api/v1/community-spaces/posts/{created.json()['id']}/convert-to-report",
            headers=headers, json={"category": "Infrastructure", "address": "Beside the community market entrance"},
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_community_video_upload_is_private(self):
        headers = self.create_user("citizen")
        post = self.client.post(f"/api/v1/community-spaces/{self.community_code}/posts", headers=headers, json={"body": "Short video showing the damaged bridge."})
        post_id = post.json()["id"]
        video = b"\x00\x00\x00\x18ftypisom" + b"community-video-test"
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"COMMUNITY_MEDIA_DIR": directory}):
            uploaded = self.client.post(
                f"/api/v1/community-spaces/posts/{post_id}/attachments",
                headers=headers, files={"file": ("bridge.mp4", video, "video/mp4")},
            )
            self.assertEqual(uploaded.status_code, 201, uploaded.text)
            attachment_id = uploaded.json()["id"]
            downloaded = self.client.get(f"/api/v1/community-spaces/posts/{post_id}/attachments/{attachment_id}", headers=headers)
            self.assertEqual(downloaded.status_code, 200)
            self.assertEqual(downloaded.content, video)
            self.assertEqual(downloaded.headers["cache-control"], "private, no-store")


    def test_community_photo_is_carried_into_official_report_evidence(self):
        headers = self.create_user("citizen")
        post = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/posts",
            headers=headers, json={"body": "Photo evidence of the damaged public drain."},
        )
        post_id = post.json()["id"]
        image_bytes = b"\xff\xd8\xff" + b"community-report-evidence"
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "COMMUNITY_MEDIA_DIR": directory,
            "REPORT_ATTACHMENT_DIR": directory + "/report-evidence",
        }):
            uploaded = self.client.post(
                f"/api/v1/community-spaces/posts/{post_id}/images",
                headers=headers, files={"file": ("drain.jpg", image_bytes, "image/jpeg")},
            )
            self.assertEqual(uploaded.status_code, 201, uploaded.text)
            converted = self.client.post(
                f"/api/v1/community-spaces/posts/{post_id}/convert-to-report",
                headers=headers,
                json={"category": "Infrastructure", "address": "Beside the community market"},
            )
            self.assertEqual(converted.status_code, 201, converted.text)
            db = self.Session()
            evidence = db.query(ReportAttachment).filter(
                ReportAttachment.report_id == converted.json()["report_id"]
            ).all()
            self.assertEqual(len(evidence), 1)
            evidence_id = evidence[0].id
            db.close()
            downloaded = self.client.get(
                f"/api/v1/reports/{converted.json()['report_id']}/attachments/{evidence_id}/download",
                headers=headers,
            )
            self.assertEqual(downloaded.status_code, 200)
            self.assertEqual(downloaded.content, image_bytes)


    def test_joined_member_receives_live_websocket_post_events(self):
        headers = self.create_user("citizen")
        token = headers["Authorization"].split(" ", 1)[1]
        with self.client.websocket_connect(
            f"/api/v1/community-spaces/{self.community_code}/live"
        ) as websocket:
            websocket.send_json({"type": "authenticate", "token": token})
            connected = websocket.receive_json()
            self.assertEqual(connected["type"], "connected")
            self.assertEqual(connected["community_code"], self.community_code)
            created = self.client.post(
                f"/api/v1/community-spaces/{self.community_code}/posts",
                headers=headers, json={"body": "Live update from a community member"},
            )
            self.assertEqual(created.status_code, 201)
            event = websocket.receive_json()
            self.assertEqual(event["type"], "post_created")
            self.assertEqual(event["post_id"], created.json()["id"])

    def test_discussion_endpoints_require_authentication(self):
        response = self.client.get(f"/api/v1/community-spaces/{self.community_code}/posts")
        self.assertEqual(response.status_code, 401)



    def test_chat_photo_upload_is_member_only_and_download_is_private(self):
        member_headers = self.create_user("citizen")
        outsider_headers = self.create_user("citizen", join=False)
        image_bytes = b"\xff\xd8\xff" + b"community-chat-photo"
        rejected_upload = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages/image",
            headers=outsider_headers, data={"body": ""},
            files={"file": ("streetlight.jpg", image_bytes, "image/jpeg")},
        )
        self.assertEqual(rejected_upload.status_code, 403)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"COMMUNITY_MEDIA_DIR": directory}):
            uploaded = self.client.post(
                f"/api/v1/community-spaces/{self.community_code}/chat/messages/image",
                headers=member_headers,
                data={"body": "The damaged streetlight."},
                files={"file": ("streetlight.jpg", image_bytes, "image/jpeg")},
            )
            self.assertEqual(uploaded.status_code, 201, uploaded.text)
            self.assertEqual(uploaded.json()["body"], "The damaged streetlight.")
            self.assertEqual(uploaded.json()["image_content_type"], "image/jpeg")
            message_id = uploaded.json()["id"]
            history = self.client.get(
                f"/api/v1/community-spaces/{self.community_code}/chat/messages",
                headers=member_headers,
            )
            self.assertEqual(history.status_code, 200)
            self.assertEqual(history.json()[0]["image_id"], message_id)
            downloaded = self.client.get(
                f"/api/v1/community-spaces/{self.community_code}/chat/messages/{message_id}/image",
                headers=member_headers,
            )
            self.assertEqual(downloaded.status_code, 200)
            self.assertEqual(downloaded.content, image_bytes)
            self.assertEqual(downloaded.headers["cache-control"], "private, no-store")
            denied = self.client.get(
                f"/api/v1/community-spaces/{self.community_code}/chat/messages/{message_id}/image",
                headers=outsider_headers,
            )
            self.assertEqual(denied.status_code, 403)

    def test_chat_photo_rejects_invalid_file_type(self):
        headers = self.create_user("citizen")
        response = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages/image",
            headers=headers,
            data={"body": ""},
            files={"file": ("not-image.txt", b"not an image", "text/plain")},
        )
        self.assertEqual(response.status_code, 415)


    def test_public_state_and_lga_feed_is_readable_without_chat_membership_or_login(self):
        member_headers = self.create_user("citizen")
        created = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/posts",
            headers=member_headers, json={"body": "Public update from Otukpo."},
        )
        self.assertEqual(created.status_code, 201, created.text)

        state_feed = self.client.get("/api/v1/community-spaces/public-feed?state_code=NG025")
        self.assertEqual(state_feed.status_code, 200, state_feed.text)
        state_posts = state_feed.json()
        self.assertIn(created.json()["id"], [post["id"] for post in state_posts])
        item = next(post for post in state_posts if post["id"] == created.json()["id"])
        self.assertEqual(item["lga_code"], "NG025011")
        self.assertEqual(item["body"], "Public update from Otukpo.")

        lga_feed = self.client.get(
            "/api/v1/community-spaces/public-feed?state_code=NG025&lga_code=NG025011"
        )
        self.assertEqual(lga_feed.status_code, 200, lga_feed.text)
        self.assertIn(created.json()["id"], [post["id"] for post in lga_feed.json()])

    def test_public_feed_rejects_lga_outside_selected_state(self):
        response = self.client.get(
            "/api/v1/community-spaces/public-feed?state_code=NG025&lga_code=NG001001"
        )
        self.assertEqual(response.status_code, 404)



if __name__ == "__main__":
    unittest.main()


    def test_community_chat_persists_messages_and_requires_membership(self):
        member_headers = self.create_user("citizen")
        sent = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=member_headers, json={"body": "Good evening, neighbours."},
        )
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(sent.json()["body"], "Good evening, neighbours.")
        self.assertEqual(sent.json()["author"]["full_name"], "Citizen User")
        history = self.client.get(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=member_headers,
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()), 1)
        self.assertEqual(history.json()[0]["id"], sent.json()["id"])
        outsider_headers = self.create_user("citizen", join=False)
        denied_read = self.client.get(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=outsider_headers,
        )
        denied_send = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=outsider_headers, json={"body": "I should not be able to send this."},
        )
        self.assertEqual(denied_read.status_code, 403)
        self.assertEqual(denied_send.status_code, 403)

    def test_community_chat_rejects_blank_messages_and_supports_history_cursor(self):
        headers = self.create_user("citizen")
        blank = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=headers, json={"body": "   "},
        )
        self.assertEqual(blank.status_code, 422)
        first = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=headers, json={"body": "First message"},
        )
        second = self.client.post(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages",
            headers=headers, json={"body": "Second message"},
        )
        older = self.client.get(
            f"/api/v1/community-spaces/{self.community_code}/chat/messages?before_id={second.json()['id']}",
            headers=headers,
        )
        self.assertEqual([item["id"] for item in older.json()], [first.json()["id"]])
