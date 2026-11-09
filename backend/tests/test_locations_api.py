import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.location import LocalGovernmentArea, State
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
