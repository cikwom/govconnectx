import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.audit_event import AuditEvent
from app.models.location import Community, LocalGovernmentArea, State, Ward
from app.models.user import User
from app.routers.locations import seed_location_directory


class LocationDirectoryTests(unittest.TestCase):
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
        db = self.Session()
        seed_location_directory(db)
        db.close()

    def admin_headers(self):
        email = f"geo-admin-{uuid4().hex}@example.com"
        db = self.Session()
        try:
            db.add(User(email=email, full_name="Geography Admin", password_hash=hash_password("Test-Password-123"), role="system_admin", is_active=True))
            db.commit()
        finally:
            db.close()
        login = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Test-Password-123"})
        self.assertEqual(login.status_code, 200)
        return {"Authorization": "Bearer " + login.json()["access_token"]}

    def test_geography_csv_preview_then_atomic_import_with_provenance(self):
        headers = self.admin_headers()
        csv_content = "record_type,code,name,parent_code\\nward,TEST-WARD-BULK,Test Ward,NG025011\\ncommunity,TEST-COMM-BULK,Test Community,TEST-WARD-BULK\\n"
        form = {"source_name": "INEC published register", "source_reference": "Official reference document 2026", "effective_from": "2026-01-01"}
        preview = self.client.post("/api/v1/locations/admin/import/preview", headers=headers,
                                   data=form, files={"file": ("locations.csv", csv_content, "text/csv")})
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview.json()["can_import"])
        self.assertEqual(preview.json()["wards"], 1)
        self.assertEqual(preview.json()["communities"], 1)
        db = self.Session()
        try:
            self.assertIsNone(db.get(Ward, "TEST-WARD-BULK"))
            self.assertIsNone(db.get(Community, "TEST-COMM-BULK"))
        finally:
            db.close()

        committed = self.client.post("/api/v1/locations/admin/import/commit", headers=headers,
                                     data=form, files={"file": ("locations.csv", csv_content, "text/csv")})
        self.assertEqual(committed.status_code, 200)
        self.assertEqual(committed.json()["imported"], 2)
        db = self.Session()
        try:
            ward = db.get(Ward, "TEST-WARD-BULK")
            community = db.get(Community, "TEST-COMM-BULK")
            self.assertEqual(ward.source_name, "INEC published register")
            self.assertEqual(ward.source_reference, "Official reference document 2026")
            self.assertEqual(ward.imported_by_user_id, int(headers["Authorization"].split(".")[1] != ""))
            self.assertEqual(community.ward_code, ward.code)
            self.assertEqual(community.source_name, "INEC published register")
            self.assertTrue(db.query(AuditEvent).filter(AuditEvent.action == "geography.bulk_imported").first())
        finally:
            db.close()

    def test_geography_csv_import_rejects_invalid_parent_without_partial_writes(self):
        headers = self.admin_headers()
        csv_content = "record_type,code,name,parent_code\\nward,TEST-WARD-INVALID,Invalid Ward,UNKNOWN-LGA\\ncommunity,TEST-COMM-INVALID,Invalid Community,TEST-WARD-INVALID\\n"
        form = {"source_name": "Official register", "source_reference": "Reference document"}
        preview = self.client.post("/api/v1/locations/admin/import/preview", headers=headers,
                                   data=form, files={"file": ("invalid.csv", csv_content, "text/csv")})
        self.assertEqual(preview.status_code, 200)
        self.assertFalse(preview.json()["can_import"])
        rejected = self.client.post("/api/v1/locations/admin/import/commit", headers=headers,
                                    data=form, files={"file": ("invalid.csv", csv_content, "text/csv")})
        self.assertEqual(rejected.status_code, 422)
        db = self.Session()
        try:
            self.assertIsNone(db.get(Ward, "TEST-WARD-INVALID"))
            self.assertIsNone(db.get(Community, "TEST-COMM-INVALID"))
        finally:
            db.close()

    def test_geography_csv_import_is_system_admin_only(self):
        registered = self.client.post("/api/v1/auth/register", json={"email": "geo-citizen-import@example.com", "full_name": "Citizen", "password": "Strong-Test-Password-42"})
        self.assertEqual(registered.status_code, 201)
        login = self.client.post("/api/v1/auth/login", json={"email": "geo-citizen-import@example.com", "password": "Strong-Test-Password-42"})
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        response = self.client.post("/api/v1/locations/admin/import/preview", headers=headers,
                                    data={"source_name": "Source", "source_reference": "Document"},
                                    files={"file": ("data.csv", "record_type,code,name,parent_code\\n", "text/csv")})
        self.assertEqual(response.status_code, 403)

    def test_directory_contains_37_states_and_774_lgas(self):
        db = self.Session()
        try:
            self.assertEqual(db.query(State).count(), 37)
            self.assertEqual(db.query(LocalGovernmentArea).count(), 774)
        finally:
            db.close()

    def test_state_list_includes_geopolitical_zone(self):
        response = self.client.get("/api/v1/locations/states")
        self.assertEqual(response.status_code, 200)
        lagos = next(item for item in response.json() if item["name"] == "Lagos")
        self.assertEqual(lagos["geopolitical_zone"], "South West")

    def test_lga_list_is_scoped_to_selected_state(self):
        response = self.client.get("/api/v1/locations/states/NG025/lgas")
        self.assertEqual(response.status_code, 200)
        names = {item["name"] for item in response.json()}
        self.assertIn("Ikeja", names)
        self.assertEqual(len(response.json()), 20)
        self.assertTrue(all(item["state_code"] == "NG025" for item in response.json()))

    def test_unknown_state_returns_404(self):
        response = self.client.get("/api/v1/locations/states/UNKNOWN/lgas")
        self.assertEqual(response.status_code, 404)


    def test_registration_saves_home_state_and_lga(self):
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "lagos-citizen@example.com",
                "full_name": "Lagos Citizen",
                "password": "Strong-Test-Password-42",
                "home_state_code": "ng025",
                "home_lga_code": "ng025011",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["home_state_code"], "NG025")
        self.assertEqual(response.json()["home_lga_code"], "NG025011")

    def test_registration_rejects_lga_from_another_state(self):
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-area@example.com",
                "full_name": "Invalid Area",
                "password": "Strong-Test-Password-42",
                "home_state_code": "NG025",
                "home_lga_code": "NG001001",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_report_location_is_independent_of_home_location(self):
        registered = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "cross-state-reporter@example.com",
                "full_name": "Cross State Reporter",
                "password": "Strong-Test-Password-42",
                "home_state_code": "NG001",
                "home_lga_code": "NG001001",
            },
        )
        self.assertEqual(registered.status_code, 201)
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "cross-state-reporter@example.com", "password": "Strong-Test-Password-42"},
        )
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        created = self.client.post(
            "/api/v1/reports",
            headers=headers,
            json={
                "title": "Road damage in Ikeja",
                "description": "A damaged road needs attention",
                "category": "Roads and Transport",
                "latitude": 6.6,
                "longitude": 3.35,
                "incident_state_code": "NG025",
                "incident_lga_code": "NG025011",
            },
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["incident_state_code"], "NG025")
        self.assertEqual(created.json()["incident_lga_code"], "NG025011")

    def test_report_rejects_lga_from_another_state(self):
        registered = self.client.post(
            "/api/v1/auth/register",
            json={"email": "bad-report-area@example.com", "full_name": "Reporter", "password": "Strong-Test-Password-42"},
        )
        self.assertEqual(registered.status_code, 201)
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "bad-report-area@example.com", "password": "Strong-Test-Password-42"},
        )
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        response = self.client.post(
            "/api/v1/reports",
            headers=headers,
            json={
                "title": "Invalid location",
                "description": "Location hierarchy should fail",
                "category": "Infrastructure",
                "latitude": 6.5,
                "longitude": 3.3,
                "incident_state_code": "NG025",
                "incident_lga_code": "NG001001",
            },
        )
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
