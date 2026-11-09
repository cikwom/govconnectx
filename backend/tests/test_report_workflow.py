import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.department_geographic_scope import DepartmentGeographicScope
from app.models.report import Report
from app.models.report_assignment import ReportAssignment
from app.models.report_history import ReportComment, ReportStatusHistory
from app.models.notification import Notification
from app.models.user import User
from app.routers.locations import seed_location_directory

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
        seed_location_directory(db)
        # Delete dependent workflow rows first so the suite also works with
        # SQLite foreign-key enforcement enabled.
        db.query(DepartmentGeographicScope).delete()
        for model in (Notification, ReportComment, ReportStatusHistory, ReportAssignment):
            db.query(model).delete()
        db.query(Report).delete()
        db.query(User).delete()
        db.query(Department).delete()
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

    def department(self, headers, name):
        created = self.client.post("/api/v1/departments", headers=headers, json={"name": name})
        self.assertEqual(created.status_code, 201)
        scoped = self.client.put(
            f"/api/v1/departments/{created.json()['id']}/geographic-scopes",
            headers=headers,
            json=[{"state_code": "NG025"}],
        )
        self.assertEqual(scoped.status_code, 200)
        return created

    def report(self, headers):
        response = self.client.post("/api/v1/reports", headers=headers, json={
            "title": "Blocked drain", "description": "Drain is blocked",
            "category": "Environment", "latitude": 6.5, "longitude": 3.3,
            "incident_state_code": "NG025", "incident_lga_code": "NG025011",
        })
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def test_department_creation_and_listing(self):
        _, admin = self.user("admin@example.com", "system_admin")
        created = self.department(admin, "Ministry of Works")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get("/api/v1/departments", headers=admin).status_code, 200)

    def test_assignment_sets_department_and_records_history(self):
        _, admin = self.user("admin@example.com", "system_admin")
        citizen_id, citizen = self.user("citizen@example.com", "citizen")
        report_id = self.report(citizen)
        department = self.department(admin, "Environment")
        response = self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":department.json()["id"],"note":"Please inspect"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["department_id"], department.json()["id"])
        self.assertEqual(self.client.get(f"/api/v1/reports/{report_id}", headers=citizen).json()["status"], "ASSIGNED")

    def test_department_admin_cannot_access_other_department_report(self):
        _, admin = self.user("root@example.com", "system_admin")
        citizen_id, citizen = self.user("reporter@example.com", "citizen")
        report_id = self.report(citizen)
        dep1 = self.department(admin, "Water")
        dep2 = self.department(admin, "Roads")
        _, manager = self.user("manager@example.com", "department_admin", dep2.json()["id"])
        self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":dep1.json()["id"]})
        denied = self.client.get(f"/api/v1/reports/{report_id}", headers=manager)
        self.assertEqual(denied.status_code, 403)

    def test_department_manager_cannot_take_report_from_another_department(self):
        _, root = self.user("root2@example.com", "system_admin")
        _, citizen = self.user("citizen2@example.com", "citizen")
        report_id = self.report(citizen)
        first = self.department(root, "First Department")
        second = self.department(root, "Second Department")
        _, manager = self.user("manager2@example.com", "department_admin", second.json()["id"])
        assigned = self.client.post(
            f"/api/v1/reports/{report_id}/assignments",
            headers=root,
            json={"department_id":first.json()["id"]},
        )
        self.assertEqual(assigned.status_code, 201)
        takeover = self.client.post(
            f"/api/v1/reports/{report_id}/assignments",
            headers=manager,
            json={"department_id":second.json()["id"]},
        )
        self.assertEqual(takeover.status_code, 403)

    def test_notifications_are_private_and_can_be_marked_read(self):
        _, root = self.user("notification-root@example.com", "system_admin")
        _, citizen = self.user("notification-citizen@example.com", "citizen")
        report_id = self.report(citizen)
        department = self.department(root, "Notification Test Department")
        assigned = self.client.post(
            f"/api/v1/reports/{report_id}/assignments",
            headers=root,
            json={"department_id":department.json()["id"]},
        )
        self.assertEqual(assigned.status_code, 201)

        inbox = self.client.get("/api/v1/notifications", headers=citizen)
        self.assertEqual(inbox.status_code, 200)
        self.assertEqual(len(inbox.json()), 1)
        notification_id = inbox.json()[0]["id"]
        self.assertEqual(self.client.get("/api/v1/notifications/unread-count", headers=citizen).json()["unread_count"], 1)
        self.assertEqual(self.client.get("/api/v1/notifications", headers=root).json(), [])

        marked = self.client.patch(f"/api/v1/notifications/{notification_id}/read", headers=citizen)
        self.assertEqual(marked.status_code, 200)
        self.assertTrue(marked.json()["is_read"])
        self.assertEqual(self.client.get("/api/v1/notifications/unread-count", headers=citizen).json()["unread_count"], 0)

        sla = self.client.get("/api/v1/sla/summary", headers=citizen)
        self.assertEqual(sla.status_code, 200)
        self.assertEqual(sla.json()["active_reports"], 1)
        self.assertEqual(sla.json()["without_sla_deadline"], 0)

    def test_status_transition_and_history(self):
        _, admin = self.user("root@example.com", "system_admin")
        _, citizen = self.user("reporter@example.com", "citizen")
        report_id = self.report(citizen)
        assigned_dep = self.department(admin, "Transport")
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
        department = self.department(admin, "Public Health")
        self.client.post(f"/api/v1/reports/{report_id}/assignments", headers=admin, json={"department_id":department.json()["id"]})
        staff_comment = self.client.post(f"/api/v1/reports/{report_id}/comments", headers=admin, json={"body":"Internal investigation note","is_internal":True})
        self.assertEqual(staff_comment.status_code, 201)
        citizen_comments = self.client.get(f"/api/v1/reports/{report_id}/comments", headers=citizen)
        self.assertEqual(citizen_comments.json(), [])

    def test_staff_cannot_access_report_after_department_scope_excludes_its_lga(self):
        _, admin = self.user("scope-admin@example.com", "system_admin")
        _, citizen = self.user("scope-citizen@example.com", "citizen")
        report_id = self.report(citizen)
        department = self.department(admin, "Lagos Area Services")
        assigned = self.client.post(
            f"/api/v1/reports/{report_id}/assignments",
            headers=admin,
            json={"department_id": department.json()["id"]},
        )
        self.assertEqual(assigned.status_code, 201)

        _, manager = self.user("scope-manager@example.com", "department_admin", department.json()["id"])
        narrowed = self.client.put(
            f"/api/v1/departments/{department.json()['id']}/geographic-scopes",
            headers=admin,
            json=[{"state_code": "NG001"}],
        )
        self.assertEqual(narrowed.status_code, 200)

        denied = self.client.get(f"/api/v1/reports/{report_id}", headers=manager)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.client.get("/api/v1/reports", headers=manager).json(), [])
        self.assertEqual(self.client.get(f"/api/v1/reports/{report_id}", headers=citizen).status_code, 200)

    def test_admin_rejects_lga_that_does_not_belong_to_selected_state(self):
        _, admin = self.user("scope-validation-admin@example.com", "system_admin")
        department = self.client.post(
            "/api/v1/departments",
            headers=admin,
            json={"name": "Scope Validation Department"},
        )
        response = self.client.put(
            f"/api/v1/departments/{department.json()['id']}/geographic-scopes",
            headers=admin,
            json=[{"state_code": "NG025", "lga_code": "NG001001"}],
        )
        self.assertEqual(response.status_code, 400)


    def test_report_auto_routes_when_one_department_matches_category_and_area(self):
        _, admin = self.user("auto-route-admin@example.com", "system_admin")
        _, citizen = self.user("auto-route-citizen@example.com", "citizen")
        department = self.department(admin, "Environmental Services")
        configured = self.client.put(
            f"/api/v1/departments/{department.json()['id']}/routing-categories",
            headers=admin,
            json=[{"category": "Environment"}],
        )
        self.assertEqual(configured.status_code, 200)

        _, manager = self.user("auto-route-manager@example.com", "department_admin", department.json()["id"])
        report_id = self.report(citizen)
        report = self.client.get(f"/api/v1/reports/{report_id}", headers=citizen).json()
        self.assertEqual(report["department_id"], department.json()["id"])
        self.assertEqual(report["status"], "ASSIGNED")
        inbox = self.client.get("/api/v1/notifications", headers=manager)
        self.assertTrue(any(item["report_id"] == report_id for item in inbox.json()))

    def test_ambiguous_category_route_stays_in_national_triage_queue(self):
        _, admin = self.user("ambiguous-route-admin@example.com", "system_admin")
        _, citizen = self.user("ambiguous-route-citizen@example.com", "citizen")
        first = self.department(admin, "Environment Department One")
        second = self.department(admin, "Environment Department Two")
        for department in (first, second):
            response = self.client.put(
                f"/api/v1/departments/{department.json()['id']}/routing-categories",
                headers=admin,
                json=[{"category": "Environment"}],
            )
            self.assertEqual(response.status_code, 200)

        report_id = self.report(citizen)
        report = self.client.get(f"/api/v1/reports/{report_id}", headers=citizen).json()
        self.assertIsNone(report["department_id"])
        self.assertEqual(report["status"], "SUBMITTED")

        queue = self.client.get("/api/v1/admin/reports/unassigned", headers=admin)
        self.assertEqual(queue.status_code, 200)
        self.assertTrue(any(item["id"] == report_id for item in queue.json()["items"]))


if __name__ == "__main__":
    unittest.main()
