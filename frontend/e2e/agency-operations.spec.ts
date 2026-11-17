import { expect, test } from "@playwright/test";

const manager = {
  id: 52, email: "manager@example.test", full_name: "Department Manager",
  role: "department_admin", department_id: 5, is_active: true,
};
const officer = { id: 88, full_name: "Field Officer", role: "official" };
const report = {
  id: 701, title: "Blocked drainage on Market Road",
  description: "Floodwater is collecting beside the market.",
  category: "Environment", latitude: 6.6018, longitude: 3.3515,
  gps_latitude: null, gps_longitude: null, address: "Market Road, Ikeja",
  incident_state_code: "LA", incident_lga_code: "IKE",
  incident_ward_code: "IKE-01", incident_community_code: "IKE-01-A",
  department_id: 5, status: "ASSIGNED", sla_due_at: "2026-11-20T10:00:00Z",
  resolved_at: null, created_at: "2026-11-17T10:00:00Z", updated_at: "2026-11-17T10:00:00Z",
};

test("department staff receive a scoped queue and can assign and progress a report", async ({ page }) => {
  const assignments: Array<Record<string, unknown>> = [];
  const statusUpdates: Array<Record<string, unknown>> = [];
  let currentReport = { ...report };

  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();

    if (path === "/api/v1/auth/login" && method === "POST") {
      return route.fulfill({ json: { access_token: "staff-e2e-token", token_type: "bearer", user: manager } });
    }
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
    } });
    if (path === "/api/v1/reports" && method === "GET") return route.fulfill({ json: [currentReport] });
    if (path === "/api/v1/reports/701" && method === "GET") return route.fulfill({ json: currentReport });
    if (path === "/api/v1/reports/701/history") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/comments") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/attachments") return route.fulfill({ json: [] });
    if (path === "/api/v1/departments/me/performance") return route.fulfill({ json: {
      department_id: 5, scope: "department", total_reports: 1, open_reports: 1,
      resolved_reports: 0, overdue_reports: 0, resolution_rate_percent: 0,
      average_resolution_hours: null, status_counts: { ASSIGNED: 1 },
      measurement_note: "Test fixture metrics for authorised reports.",
    } });
    if (path === "/api/v1/departments/5/members") return route.fulfill({ json: [officer] });
    if (path === "/api/v1/reports/701/assignments" && method === "POST") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      assignments.push(body);
      return route.fulfill({ status: 201, json: {
        id: 1001, report_id: 701, department_id: 5, assigned_to_user_id: 88,
        assigned_by_user_id: 52, note: body.note, created_at: "2026-11-17T12:00:00Z",
      } });
    }
    if (path === "/api/v1/reports/701/status" && method === "PATCH") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      statusUpdates.push(body);
      currentReport = { ...currentReport, status: String(body.status), updated_at: "2026-11-17T12:05:00Z" };
      return route.fulfill({ json: currentReport });
    }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill("manager@example.test");
  await page.getByLabel("Password").fill("ManagerTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();

  await expect(page).toHaveURL(/\/agency$/);
  await expect(page.getByRole("heading", { name: "Department report queue" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Blocked drainage on Market Road" })).toBeVisible();
  await expect(page.getByText("Reports in scope")).toBeVisible();

  await page.getByRole("link", { name: /Blocked drainage on Market Road/ }).click();
  await expect(page.getByRole("heading", { name: "Officer operations" })).toBeVisible();
  await page.getByLabel("Field officer (optional)").selectOption("88");
  await page.getByLabel("Assignment note (optional)").fill("Inspect the blocked drainage and upload site evidence.");
  await page.getByRole("button", { name: "Save assignment" }).click();
  await expect(page.getByText("Report assignment saved.")).toBeVisible();
  expect(assignments[0]).toMatchObject({
    department_id: 5, assigned_to_user_id: 88,
    note: "Inspect the blocked drainage and upload site evidence.",
  });

  await page.getByLabel("New status").selectOption("IN_PROGRESS");
  await page.getByLabel("Public update note (optional)").fill("Field officer dispatched for inspection.");
  await page.getByRole("button", { name: "Update status" }).click();
  await expect(page.getByText("Report status updated.")).toBeVisible();
  expect(statusUpdates[0]).toMatchObject({
    status: "IN_PROGRESS", message: "Field officer dispatched for inspection.",
  });
});


test("field officers land on their individual assignment view", async ({ page }) => {
  const officerUser = { id: 88, email: "officer@example.test", full_name: "Field Officer", role: "official", department_id: 5, is_active: true };
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "officer-e2e-token", token_type: "bearer", user: officerUser } });
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
    } });
    if (path === "/api/v1/reports") return route.fulfill({ json: [{ ...report, assigned_to_user_id: 88 }] });
    if (path === "/api/v1/departments/me/performance") return route.fulfill({ json: {
      department_id: 5, scope: "individual_assignments", total_reports: 1, open_reports: 1,
      resolved_reports: 0, overdue_reports: 0, resolution_rate_percent: 0,
      average_resolution_hours: null, status_counts: { ASSIGNED: 1 },
      measurement_note: "Only this officer's assignments are included.",
    } });
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill("officer@example.test");
  await page.getByLabel("Password").fill("OfficerTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/agency$/);
  await expect(page.getByRole("heading", { name: "My field assignments" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "My assigned reports" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Blocked drainage on Market Road/ })).toBeVisible();
});
