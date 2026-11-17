import { expect, test } from "@playwright/test";

const citizen = {
  id: 41, email: "citizen@example.test", full_name: "Test Citizen",
  role: "citizen", is_active: true,
};
const report = {
  id: 701, title: "Blocked drainage on Market Road",
  description: "Floodwater is collecting beside the market after rainfall.",
  category: "Infrastructure", latitude: 6.6018, longitude: 3.3515,
  gps_latitude: null, gps_longitude: null, address: "Market Road, Ikeja",
  incident_state_code: "LA", incident_lga_code: "IKE",
  incident_ward_code: "IKE-01", incident_community_code: "IKE-01-A",
  department_id: null, status: "RESOLVED", sla_due_at: null,
  resolved_at: "2026-11-16T10:00:00Z",
  created_at: "2026-11-10T10:00:00Z", updated_at: "2026-11-16T10:00:00Z",
};

test("citizen can review a resolved report, upload evidence, request escalation and submit feedback", async ({ page }) => {
  let attachments: Array<Record<string, unknown>> = [];
  const escalationRequests: Array<Record<string, unknown>> = [];
  const feedbackRequests: Array<Record<string, unknown>> = [];
  let uploadCount = 0;

  await page.route("http://localhost:8000/api/v1/**", async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();

    if (path === "/api/v1/auth/login" && method === "POST") {
      return route.fulfill({ json: { access_token: "citizen-e2e-token", token_type: "bearer", user: citizen } });
    }
    if (path === "/api/v1/preferences") {
      return route.fulfill({ json: {
        email_notifications: true, in_app_notifications: true, sms_notifications: false,
        sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
        phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
      } });
    }
    if (path === "/api/v1/reports" && method === "GET") return route.fulfill({ json: [report] });
    if (path === "/api/v1/reports/701" && method === "GET") return route.fulfill({ json: report });
    if (path === "/api/v1/reports/701/history") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/comments") return route.fulfill({ json: [] });
    if (path === "/api/v1/reports/701/attachments" && method === "GET") return route.fulfill({ json: attachments });
    if (path === "/api/v1/reports/701/duplicate-hint") {
      return route.fulfill({ json: {
        possible_duplicate_count: 1, review_recommended: true,
        message: "A similar report may already exist. Please review it before submitting another report.",
      } });
    }
    if (path === "/api/v1/reports/701/attachments" && method === "POST") {
      uploadCount += 1;
      attachments = [{
        id: 801, report_id: 701, uploaded_by_user_id: 41,
        original_filename: "drainage-evidence.png", content_type: "image/png",
        size_bytes: 20, sha256: "test-fixture-hash",
        created_at: "2026-11-17T12:00:00Z",
      }];
      return route.fulfill({ status: 201, json: attachments[0] });
    }
    if (path === "/api/v1/reports/701/escalations" && method === "POST") {
      escalationRequests.push(route.request().postDataJSON() as Record<string, unknown>);
      return route.fulfill({ status: 201, json: {
        id: 901, status: "OPEN", notice: "Your escalation request has been recorded for administrator review.",
      } });
    }
    if (path === "/api/v1/reports/701/feedback" && method === "POST") {
      feedbackRequests.push(route.request().postDataJSON() as Record<string, unknown>);
      return route.fulfill({ status: 201, json: { id: 902, report_id: 701, rating: 4, comment: "The repair was completed." } });
    }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/login");
  await page.getByLabel("Email address").fill("citizen@example.test");
  await page.getByLabel("Password").fill("CitizenTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByRole("link", { name: /Blocked drainage on Market Road/ }).click();
  await expect(page.getByRole("heading", { name: "Blocked drainage on Market Road" })).toBeVisible();
  await expect(page.getByText(/A similar report may already exist/)).toBeVisible();

  await page.locator("#evidence-file").setInputFiles({
    name: "drainage-evidence.png",
    mimeType: "image/png",
    buffer: Buffer.from("synthetic evidence fixture"),
  });
  await page.getByRole("button", { name: "Upload evidence" }).click();
  await expect(page.getByText("drainage-evidence.png")).toBeVisible();
  expect(uploadCount).toBe(1);

  await page.getByLabel("Urgency").selectOption("critical");
  await page.getByLabel("Why does this need attention?").fill("The flooding has returned and is affecting nearby homes.");
  await page.getByRole("button", { name: "Request escalation" }).click();
  await expect(page.getByText("Your escalation request has been recorded for administrator review.")).toBeVisible();
  expect(escalationRequests[0]).toMatchObject({
    urgency: "critical",
    reason: "The flooding has returned and is affecting nearby homes.",
  });

  await page.getByLabel("Rating").selectOption("4");
  await page.getByLabel("Comments (optional)").fill("The repair was completed.");
  await page.getByRole("button", { name: "Submit feedback" }).click();
  await expect(page.getByText("Thank you. Your feedback has been recorded.")).toBeVisible();
  expect(feedbackRequests[0]).toMatchObject({ rating: 4, comment: "The repair was completed." });
});
