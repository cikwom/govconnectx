import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.report import Report
from app.models.user import User

class ReportWorkflowTests(unittest.TestCase):
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
        for model in (Report, User, Department):
            db.query(model).delete()
        db.commit()
        db.close()

    def user(self, email, role, department_id=None):
        db = self.Session()
        user = User(email=email, full_name=email.split("@")[0], password_hash=hash_password("Strong-Test-Password-42"), role=role, department_id=department_id, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        db.close()
        response = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Strong-Test-Password-42"})
        return user_id, {"Authorization": "Bearer " + response.json()["access_token"]}

    def report(self, headers):
        return self.client.post("/api/v1/reports", headers=headers, json={"title":"Blocked drain","description":"Drain is blocked","category":"Environment","latitude":6.5,"longitude":3.3}).json()["id"]

    def test_department_creation_and_listing(self):
        _, admin = self.user("admin@example.com", "system_admin")
        created = self.client.post("/api/v1/departments", headers=admin, json={"name":"Ministry of Works"})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get("/api/v1/departments", headers=admin).status_code, 200)

    def test_assignment_sets_department_and_records_history(self):
        _, admin = self.user("admin@example.com", "system_admin")
        citizen_id, citizen = self.user("citizen@example.com", "citizen")
        report_id = self.report(citizen)
        department = self.client.post("/api/v1/departments", headers=admin, json={"name":"Environment"})
        response = self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":department.json()["id"],"note":"Please inspect"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["department_id"], department.json()["id"])
        self.assertEqual(self.client.get(f"/api/v1/reports/{report_id}", headers=citizen).json()["status"], "ASSIGNED")

    def test_department_admin_cannot_access_other_department_report(self):
        _, admin = self.user("root@example.com", "system_admin")
        citizen_id, citizen = self.user("reporter@example.com", "citizen")
        report_id = self.report(citizen)
        dep1 = self.client.post("/api/v1/departments", headers=admin, json={"name":"Water"})
        dep2 = self.client.post("/api/v1/departments", headers=admin, json={"name":"Roads"})
        _, manager = self.user("manager@example.com", "department_admin", dep2.json()["id"])
        self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":dep1.json()["id"]})
        denied = self.client.get(f"/api/v1/reports/{report_id}", headers=manager)
        self.assertEqual(denied.status_code, 403)

    def test_status_transition_and_history(self):
        _, admin = self.user("root@example.com", "system_admin")
        _, citizen = self.user("reporter@example.com", "citizen")
        report_id = self.report(citizen)
        assigned_dep = self.client.post("/api/v1/departments", headers=admin, json={"name":"Transport"})
        self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":assigned_dep.json()["id"]})
        updated = self.client.patch(f"/api/v1/reports/{report_id}/status", headers=admin, json={"status":"IN_PROGRESS","message":"Work started"})
        self.assertEqual(updated.status_code, 200)
        history = self.client.get(f"/api/v1/reports/{report_id}/history", headers=citizen)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()[-1]["new_status"], "IN_PROGRESS")
        invalid = self.client.patch(f"/api/v1/reports/{report_id}/status", headers=admin, json={"status":"SUBMITTED"})
        self.assertEqual(invalid.status_code, 400)

    def test_internal_comments_hidden_from_citizens(self):
        _, admin = self.user("root@example.com", "system_admin")
        _, citizen = self.user("reporter@example.com", "citizen")
        report_id = self.report(citizen)
        department = self.client.post("/api/v1/departments", headers=admin, json={"name":"Public Health"})
        self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":department.json()["id"]})
        staff_comment = self.client.post(f"/api/v1/reports/{report_id}/comments", headers=admin, json={"body":"Internal investigation note","is_internal":True})
        self.assertEqual(staff_comment.status_code, 201)
        citizen_comments = self.client.get(f"/api/v1/reports/{report_id}/comments", headers=citizen)
        self.assertEqual(citizen_comments.json(), [])

if __name__ == "__main__":
    unittest.main()
