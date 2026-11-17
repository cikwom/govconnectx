import { expect, test } from "@playwright/test";

const admin = { id: 1, email: "admin@example.test", full_name: "Platform Admin", role: "system_admin", is_active: true };
const staff = {
  id: 77, email: "officer@example.test", full_name: "Field Officer",
  role: "official", is_active: true, department_id: null,
  reports_submitted: 0, created_at: "2026-11-01T10:00:00Z",
};
const department = { id: 5, name: "Public Works", code: "PUBLIC-WORKS", is_active: true };

test("system admin can assign a field officer to a department", async ({ page }) => {
  const assignments: Array<Record<string, unknown>> = [];
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();

    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "admin-department-token", token_type: "bearer", user: admin } });
    if (path === "/api/v1/auth/me") return route.fulfill({ json: admin });
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
    } });
    if (path === "/api/v1/departments" && method === "GET") return route.fulfill({ json: [department] });
    if (path === "/api/v1/departments/members/77" && method === "PATCH") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      assignments.push(body);
      return route.fulfill({ json: { user_id: 77, department_id: body.department_id } });
    }
    if (path === "/api/v1/admin/overview") return route.fulfill({ json: {
      users: { total: 2, active: 2, inactive: 0, by_role: { system_admin: 1, official: 1 }, registered_today: 0 },
      reports: { total: 0, by_status: {}, open: 0, overdue: 0 },
    } });
    if (path === "/api/v1/admin/users") return route.fulfill({ json: { items: [
      { ...admin, reports_submitted: 0, created_at: "2026-10-01T10:00:00Z" }, staff,
    ] } });
    if (path === "/api/v1/admin/reports") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/activity") return route.fulfill({ json: [] });
    if (path === "/api/v1/admin/oversight") return route.fulfill({ json: {
      window_days: 30, thresholds: { min_reports: 3, burst_threshold: 5, burst_window_hours: 24 },
      summary: { citizens_reviewed: 0, flagged_citizens: 0, high_priority: 0, reports_analyzed: 0 },
      items: [], notice: "Test fixture",
    } });
    if (path === "/api/v1/admin/reports/location-review") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/audit-logs") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/notification-deliveries") return route.fulfill({ json: {
      summary: { by_status: {}, by_channel: {}, queued: 0, sending: 0, sent: 0, failed: 0 }, items: [],
    } });
    if (path === "/api/v1/admin/community/listings") return route.fulfill({ json: [] });
    if (path === "/api/v1/admin/geography/overview") return route.fulfill({ json: {
      country: "Nigeria", total_states: 37, total_lgas: 774, geopolitical_zones: [],
    } });
    if (path === "/api/v1/admin/reports/unassigned") return route.fulfill({ json: { total: 0, items: [] } });
    if (path === "/api/v1/locations/states") return route.fulfill({ json: [] });
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill("admin@example.test");
  await page.getByLabel("Password").fill("AdminTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Command Centre" })).toBeVisible();

  const staffRow = page.getByRole("row").filter({ hasText: "officer@example.test" });
  const departmentSelect = staffRow.getByRole("combobox", { name: "Department Field Officer" });
  await expect(departmentSelect).toBeVisible();
  await expect(departmentSelect).toHaveValue("");
  await departmentSelect.selectOption("5");
  await expect(departmentSelect).toHaveValue("5");
  await expect(page.getByRole("status").filter({ hasText: "Department assignment saved." })).toBeVisible();
  expect(assignments).toEqual([{ department_id: 5 }]);
});
