import { expect, test } from "@playwright/test";

const admin = {
  id: 1, email: "admin@example.test", full_name: "Platform Admin",
  role: "system_admin", is_active: true,
};
const citizen = {
  id: 41, email: "citizen@example.test", full_name: "Test Citizen",
  role: "citizen", is_active: true, reports_submitted: 2,
  created_at: "2026-11-01T10:00:00Z",
};
const states = [{ code: "LA", name: "Lagos", geopolitical_zone: "South West" }];
const lgas = [{ code: "IKE", name: "Ikeja", state_code: "LA" }];

test("system admin can suspend, reactivate and anonymize a citizen account with reasons", async ({ page }) => {
  let citizenActive = true;
  let citizenDeleted = false;
  const accountActions: Array<{ method: string; path: string; body?: Record<string, unknown> }> = [];

  page.on("dialog", async dialog => {
    if (dialog.type() === "prompt") {
      await dialog.accept("Verified test moderation reason");
    } else {
      await dialog.accept();
    }
  });

  await page.route("http://localhost:8000/api/v1/**", async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();

    if (path === "/api/v1/auth/login" && method === "POST") {
      return route.fulfill({ json: { access_token: "admin-e2e-token", token_type: "bearer", user: admin } });
    }
    if (path === "/api/v1/preferences") {
      return route.fulfill({ json: {
        email_notifications: true, in_app_notifications: true, sms_notifications: false,
        sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
        phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
      } });
    }
    if (path === "/api/v1/admin/overview") {
      return route.fulfill({ json: {
        users: { total: citizenDeleted ? 1 : 2, active: citizenDeleted ? 1 : (citizenActive ? 2 : 1),
          inactive: citizenDeleted || citizenActive ? 0 : 1, by_role: { citizen: citizenDeleted ? 0 : 1, system_admin: 1 }, registered_today: 0 },
        reports: { total: 0, by_status: {}, open: 0, overdue: 0 },
      } });
    }
    if (path === "/api/v1/admin/users" && method === "GET") {
      return route.fulfill({ json: { items: [
        { ...admin, reports_submitted: 0, created_at: "2026-10-01T10:00:00Z" },
        ...(!citizenDeleted ? [{ ...citizen, is_active: citizenActive }] : []),
      ] } });
    }
    if (path === "/api/v1/admin/users/41/status" && method === "PATCH") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      accountActions.push({ method, path, body });
      citizenActive = body.is_active === true;
      return route.fulfill({ json: { id: 41, is_active: citizenActive } });
    }
    if (path === "/api/v1/admin/users/41" && method === "DELETE") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      accountActions.push({ method, path, body });
      citizenDeleted = true;
      citizenActive = false;
      return route.fulfill({ json: { id: 41, role: "deleted", is_active: false } });
    }
    if (path === "/api/v1/admin/reports") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/activity") return route.fulfill({ json: [] });
    if (path === "/api/v1/admin/oversight") {
      return route.fulfill({ json: {
        window_days: 30, thresholds: { min_reports: 3, burst_threshold: 5, burst_window_hours: 24 },
        summary: { citizens_reviewed: 0, flagged_citizens: 0, high_priority: 0, reports_analyzed: 0 },
        items: [], notice: "Test fixture",
      } });
    }
    if (path === "/api/v1/admin/reports/location-review") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/audit-logs") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/notification-deliveries") {
      return route.fulfill({ json: {
        summary: { by_status: {}, by_channel: {}, queued: 0, sending: 0, sent: 0, failed: 0 },
        items: [],
      } });
    }
    if (path === "/api/v1/admin/community/listings") return route.fulfill({ json: [] });
    if (path === "/api/v1/admin/geography/overview") {
      return route.fulfill({ json: { country: "Nigeria", total_states: 37, total_lgas: 774, geopolitical_zones: [] } });
    }
    if (path === "/api/v1/admin/reports/unassigned") return route.fulfill({ json: { total: 0, items: [] } });
    if (path === "/api/v1/departments") return route.fulfill({ json: [] });
    if (path === "/api/v1/locations/states") return route.fulfill({ json: states });
    if (path === "/api/v1/locations/states/LA/lgas") return route.fulfill({ json: lgas });
    if (path === "/api/v1/locations/lgas/IKE/wards") return route.fulfill({ json: [] });
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill("admin@example.test");
  await page.getByLabel("Password").fill("AdminTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Command Centre" })).toBeVisible();

  const citizenRow = page.getByRole("row").filter({ hasText: "citizen@example.test" });
  await expect(citizenRow).toBeVisible();
  await citizenRow.getByRole("button", { name: "Suspend account" }).click();
  await expect(citizenRow.getByText("Inactive")).toBeVisible();
  await citizenRow.getByRole("button", { name: "Reactivate account" }).click();
  await expect(citizenRow.getByText("Active")).toBeVisible();
  await citizenRow.getByRole("button", { name: "Delete account" }).click();
  await expect(page.getByText("citizen@example.test")).toHaveCount(0);

  const adminRow = page.getByRole("row").filter({ hasText: "admin@example.test" });
  await expect(adminRow.getByRole("button", { name: "Delete account" })).toBeDisabled();
  expect(accountActions).toHaveLength(3);
  expect(accountActions[0].body).toMatchObject({ is_active: false, reason: "Verified test moderation reason" });
  expect(accountActions[1].body).toMatchObject({ is_active: true, reason: "Verified test moderation reason" });
  expect(accountActions[2].body).toMatchObject({ reason: "Verified test moderation reason" });
});
