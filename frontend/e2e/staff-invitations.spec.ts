import { expect, test } from "@playwright/test";

const admin = { id: 1, email: "admin@example.test", full_name: "Platform Admin", role: "system_admin", is_active: true };

test("system administrator creates and revokes a staff invitation", async ({ page }) => {
  const created: Record<string, unknown>[] = [];
  let revoked = false;
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname.replace(/\/+$/, "");
    const method = route.request().method();
    if (path === "/api/v1/auth/login") return route.fulfill({ json: { access_token: "staff-invite-token", token_type: "bearer", user: admin } });
    if (path === "/api/v1/auth/me") return route.fulfill({ json: admin });
    if (path === "/api/v1/preferences") return route.fulfill({ json: { email_notifications: true, in_app_notifications: true, sms_notifications: false, sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null, phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z" } });
    if (path === "/api/v1/departments") return route.fulfill({ json: [{ id: 5, name: "Public Works", code: "PUBLIC-WORKS", is_active: true }] });
    if (path === "/api/v1/admin/overview") return route.fulfill({ json: { users: { total: 1, active: 1, inactive: 0, by_role: { system_admin: 1 }, registered_today: 0 }, reports: { total: 0, by_status: {}, open: 0, overdue: 0 } } });
    if (path === "/api/v1/admin/users") return route.fulfill({ json: { items: [{ ...admin, reports_submitted: 0, created_at: "2026-11-01T10:00:00Z" }] } });
    if (path === "/api/v1/admin/reports") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/activity") return route.fulfill({ json: [] });
    if (path === "/api/v1/admin/oversight") return route.fulfill({ json: { window_days: 30, thresholds: { min_reports: 3, burst_threshold: 5, burst_window_hours: 24 }, summary: { citizens_reviewed: 0, flagged_citizens: 0, high_priority: 0, reports_analyzed: 0 }, items: [], notice: "Test fixture" } });
    if (path === "/api/v1/admin/reports/location-review") return route.fulfill({ json: { items: [] } });
    if (path === "/api/v1/admin/staff-invitations" && method === "GET") return route.fulfill({ json: { items: created.map((item, index) => ({ id: index + 1, email: item.email, full_name: item.full_name, role: item.role, department_id: item.department_id, expires_at: "2026-11-20T10:00:00Z", accepted_at: null, revoked_at: revoked ? "2026-11-18T10:00:00Z" : null, status: revoked ? "revoked" : "pending", created_at: "2026-11-17T10:00:00Z" })) } });
    if (path === "/api/v1/admin/staff-invitations" && method === "POST") { created.push(route.request().postDataJSON() as Record<string, unknown>); return route.fulfill({ status: 201, json: { id: 1, email: "officer@example.test", role: "official", department_id: 5, expires_at: "2026-11-20T10:00:00Z", development_invitation_url: "http://localhost:5173/staff-invitation?token=sample-token" } }); }
    if (path === "/api/v1/admin/staff-invitations/1/revoke" && method === "POST") { revoked = true; return route.fulfill({ json: { id: 1, status: "revoked" } }); }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill("admin@example.test");
  await page.getByLabel("Password").fill("AdminTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/admin$/);
  // The dashboard mounts several data panels after authentication. Wait for the
  // invitation panel's first load to finish before interacting with its form;
  // otherwise the initial React state updates can detach the input mid-fill.
  const invitationPanel = page.locator("section.panel").filter({ has: page.getByRole("heading", { name: "Staff invitations" }) });
  await expect(invitationPanel.getByText("No staff invitations yet.")).toBeVisible();
  await expect(invitationPanel.getByLabel("Department").locator("option", { hasText: "Public Works" })).toHaveCount(1);
  await invitationPanel.getByLabel("Staff full name").fill("Field Officer");
  await invitationPanel.getByLabel("Staff email").fill("officer@example.test");
  await invitationPanel.getByLabel("Staff role").selectOption("official");
  await invitationPanel.getByLabel("Department").selectOption("5");
  await invitationPanel.getByRole("button", { name: "Create staff invitation" }).click();
  await expect(page.getByText("Invitation created. Email delivery will be attempted in the background.")).toBeVisible();
  await expect(page.getByLabel("Development invitation link")).toHaveValue(/sample-token/);
  expect(created).toEqual([{ email: "officer@example.test", full_name: "Field Officer", role: "official", department_id: 5 }]);
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Revoke invitation" }).click();
  await expect(page.getByText("revoked", { exact: true })).toBeVisible();
});
