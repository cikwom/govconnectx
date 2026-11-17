import { expect, test } from "@playwright/test";

const report = {
  id: 701, title: "Blocked drainage on Market Road",
  description: "Floodwater is collecting beside the market.",
  category: "Environment", latitude: 6.6018, longitude: 3.3515,
  gps_latitude: null, gps_longitude: null, address: "Market Road, Ikeja",
  incident_state_code: "LA", incident_lga_code: "IKE",
  incident_ward_code: "IKE-01", incident_community_code: null,
  department_id: 5, status: "ASSIGNED", sla_due_at: null,
  resolved_at: null, created_at: "2026-11-17T10:00:00Z", updated_at: "2026-11-17T10:00:00Z",
};
const preferences = {
  email_notifications: true, in_app_notifications: true, sms_notifications: false,
  sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
  phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
};

test("authorised department staff can save an internal note marked private", async ({ page }) => {
  const staff = { id: 52, email: "manager@example.test", full_name: "Department Manager", role: "department_admin", department_id: 5, is_active: true };
  const posted: Array<Record<string, unknown>> = [];
  let comments: Array<Record<string, unknown>> = [];

  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "staff-note-token", token_type: "bearer", user: staff } });
    if (path === "/api/v1/preferences") return route.fulfill({ json: preferences });
    if (path === "/api/v1/reports/701" && method === "GET") return route.fulfill({ json: report });
    if (path === "/api/v1/reports/701/history") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/comments" && method === "GET") return route.fulfill({ json: comments });
    if (path === "/api/v1/reports/701/comments" && method === "POST") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      posted.push(body);
      comments = [{ id: 1002, report_id: 701, author_user_id: 52, body: body.body, is_internal: body.is_internal, created_at: "2026-11-17T12:05:00Z" }];
      return route.fulfill({ status: 201, json: comments[0] });
    }
    if (path === "/api/v1/reports/701/attachments") return route.fulfill({ json: [] });
    if (path === "/api/v1/departments/5/members") return route.fulfill({ json: [] });
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill("manager@example.test");
  await page.getByLabel("Password").fill("ManagerTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/agency$/);
  await page.goto("/reports/701");
  await expect(page.getByRole("heading", { name: "Updates and comments" })).toBeVisible();
  await page.getByPlaceholder("Write an update or ask a question…").fill("Inspection found a damaged private utility line. Coordinate with the water authority.");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Save internal note" }).click();
  await expect(page.getByText("Inspection found a damaged private utility line. Coordinate with the water authority.")).toBeVisible();
  expect(posted).toHaveLength(1);
  expect(posted[0]).toMatchObject({
    body: "Inspection found a damaged private utility line. Coordinate with the water authority.",
    is_internal: true,
  });
});

test("citizens do not receive the internal-note control", async ({ page }) => {
  const citizen = { id: 41, email: "citizen@example.test", full_name: "Test Citizen", role: "citizen", is_active: true };
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "citizen-note-token", token_type: "bearer", user: citizen } });
    if (path === "/api/v1/preferences") return route.fulfill({ json: preferences });
    if (path === "/api/v1/reports/701") return route.fulfill({ json: { ...report, user_id: 41 } });
    if (path === "/api/v1/reports/701/history") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/comments") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/attachments") return route.fulfill({ json: [] });
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/login");
  await page.getByLabel("Email address").fill("citizen@example.test");
  await page.getByLabel("Password").fill("CitizenTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto("/reports/701");
  await expect(page.getByRole("heading", { name: "Updates and comments" })).toBeVisible();
  await expect(page.locator(".internal-note-option input[type=\"checkbox\"]")).toHaveCount(0);
  await expect(page.getByText("Internal staff note")).toHaveCount(0);
});
