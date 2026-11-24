import { expect, test } from "@playwright/test";

const citizen = {
  id: 41, email: "citizen@example.test", full_name: "Test Citizen",
  role: "citizen", is_active: true, home_state_code: "LA", home_lga_code: "IKE",
};
const states = [
  { code: "LA", name: "Lagos", geopolitical_zone: "South West" },
  { code: "AB", name: "Abia", geopolitical_zone: "South East" },
];
const lgas = [{ code: "IKE", name: "Ikeja", state_code: "LA" }];
const wards = [{ code: "IKE-01", name: "Ikeja Central", lga_code: "IKE" }];
const communities = [{ code: "IKE-01-A", name: "Alausa", ward_code: "IKE-01" }];

test("citizen registration submits the selected state and LGA", async ({ page }) => {
  const registrations: Record<string, unknown>[] = [];
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/v1/locations/states") return route.fulfill({ json: states });
    if (path === "/api/v1/locations/states/LA/lgas") return route.fulfill({ json: lgas });
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
    } });
    if (path === "/api/v1/auth/register" && route.request().method() === "POST") {
      registrations.push(route.request().postDataJSON() as Record<string, unknown>);
      return route.fulfill({ status: 201, json: citizen });
    }
    if (path === "/api/v1/auth/login") {
      return route.fulfill({ json: { access_token: "e2e-test-token", token_type: "bearer", user: citizen } });
    }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/register");
  await page.getByLabel("Full name").fill("Test Citizen");
  await page.getByLabel("Email address").fill("citizen@example.test");
  await page.getByLabel("Password").fill("StrongTestPassword123");
  await page.getByLabel("State or FCT").selectOption("LA");
  await page.getByLabel("Local Government Area").selectOption("IKE");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  expect(registrations).toHaveLength(1);
  expect(registrations[0]).toMatchObject({
    email: "citizen@example.test", home_state_code: "LA", home_lga_code: "IKE",
  });
});

test("citizen signs in and submits a report with state, LGA, ward and community", async ({ page }) => {
  let created: Record<string, unknown> | undefined;
  let reports: Record<string, unknown>[] = [];
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    if (path === "/api/v1/locations/states") return route.fulfill({ json: states });
    if (path === "/api/v1/locations/states/LA/lgas") return route.fulfill({ json: lgas });
    if (path === "/api/v1/locations/lgas/IKE/wards") return route.fulfill({ json: wards });
    if (path === "/api/v1/locations/wards/IKE-01/communities") return route.fulfill({ json: communities });
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-17T12:00:00Z",
    } });
    if (path === "/api/v1/auth/login") {
      return route.fulfill({ json: { access_token: "e2e-test-token", token_type: "bearer", user: citizen } });
    }
    if (path === "/api/v1/reports" && method === "GET") return route.fulfill({ json: reports });
    if (path === "/api/v1/reports" && method === "POST") {
      created = route.request().postDataJSON() as Record<string, unknown>;
      const report = {
        id: 701, ...created, address: created.address ?? null, status: "SUBMITTED",
        sla_due_at: null, resolved_at: null,
        created_at: "2026-11-17T12:00:00Z", updated_at: "2026-11-17T12:00:00Z",
      };
      reports = [report];
      return route.fulfill({ status: 201, json: report });
    }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/login");
  await page.getByLabel("Email address").fill("citizen@example.test");
  await page.getByLabel("Password").fill("StrongTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: /Good day/ })).toBeVisible();

  await page.getByRole("button", { name: /Submit a report/ }).click();
  await page.getByLabel("Report title").fill("Blocked drainage on Market Road");
  await page.getByLabel("Description").fill("Floodwater is collecting beside the market after rainfall.");
  await page.getByLabel("Infrastructure issue").selectOption("Drainage");
  await page.getByLabel("Incident state or FCT").selectOption("LA");
  await page.getByLabel("Incident LGA").selectOption("IKE");
  await page.getByLabel("Ward (optional)").selectOption("IKE-01");
  await page.getByLabel("Community (optional)").selectOption("IKE-01-A");
  await page.getByLabel("Latitude (optional)").fill("6.6018");
  await page.getByLabel("Longitude (optional)").fill("3.3515");
  await page.getByRole("button", { name: "Submit report" }).click();

  await expect(page.getByRole("heading", { name: "Blocked drainage on Market Road" })).toBeVisible();
  expect(created).toMatchObject({
    title: "Blocked drainage on Market Road",
    incident_state_code: "LA", incident_lga_code: "IKE",
    incident_ward_code: "IKE-01", incident_community_code: "IKE-01-A",
    latitude: 6.6018, longitude: 3.3515,
  });
});


test("citizen can submit a report using a landmark without sharing GPS or coordinates", async ({ page }) => {
  let created: Record<string, unknown> | undefined;
  let reports: Record<string, unknown>[] = [];
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    if (path === "/api/v1/locations/states") return route.fulfill({ json: states });
    if (path === "/api/v1/locations/states/LA/lgas") return route.fulfill({ json: lgas });
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-24T12:00:00Z",
    } });
    if (path === "/api/v1/auth/login") {
      return route.fulfill({ json: { access_token: "e2e-test-token", token_type: "bearer", user: citizen } });
    }
    if (path === "/api/v1/reports" && method === "GET") return route.fulfill({ json: reports });
    if (path === "/api/v1/reports" && method === "POST") {
      created = route.request().postDataJSON() as Record<string, unknown>;
      const report = {
        id: 702, ...created, latitude: null, longitude: null, gps_latitude: null, gps_longitude: null,
        status: "SUBMITTED", sla_due_at: null, resolved_at: null,
        created_at: "2026-11-24T12:00:00Z", updated_at: "2026-11-24T12:00:00Z",
      };
      reports = [report];
      return route.fulfill({ status: 201, json: report });
    }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/login");
  await page.getByLabel("Email address").fill("citizen@example.test");
  await page.getByLabel("Password").fill("StrongTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByRole("button", { name: /Submit a report/ }).click();
  await page.getByLabel("Report title").fill("Flooding beside the health centre");
  await page.getByLabel("Description").fill("Water covers the pedestrian entrance after heavy rain.");
  await page.getByLabel("Category").selectOption("Environment");
  await page.getByLabel("Incident state or FCT").selectOption("LA");
  await page.getByLabel("Incident LGA").selectOption("IKE");
  await page.getByLabel("Street, landmark, nearby building or address").fill("Beside Ikeja community health centre, Alausa");
  await page.getByRole("button", { name: "Submit report" }).click();

  await expect(page.getByText("Beside Ikeja community health centre, Alausa")).toBeVisible();
  expect(created).toMatchObject({
    title: "Flooding beside the health centre",
    address: "Beside Ikeja community health centre, Alausa",
    incident_state_code: "LA", incident_lga_code: "IKE",
  });
  expect(created).not.toHaveProperty("latitude");
  expect(created).not.toHaveProperty("longitude");
  expect(created).not.toHaveProperty("gps_latitude");
  expect(created).not.toHaveProperty("gps_longitude");
});

test("citizen can join a selected community before posting", async ({ page }) => {
  await page.route("http://localhost:8000/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    if (path === "/api/v1/locations/states") return route.fulfill({ json: states });
    if (path === "/api/v1/locations/states/LA/lgas") return route.fulfill({ json: lgas });
    if (path === "/api/v1/locations/lgas/IKE/wards") return route.fulfill({ json: wards });
    if (path === "/api/v1/locations/wards/IKE-01/communities") return route.fulfill({ json: communities });
    if (path === "/api/v1/preferences") return route.fulfill({ json: {
      email_notifications: true, in_app_notifications: true, sms_notifications: false,
      sms_consent_at: null, sms_consent_revoked_at: null, phone_number: null,
      phone_verified_at: null, preferred_language: "en", updated_at: "2026-11-24T12:00:00Z",
    } });
    if (path === "/api/v1/auth/login") {
      return route.fulfill({ json: { access_token: "e2e-test-token", token_type: "bearer", user: citizen } });
    }
    if (path === "/api/v1/community-spaces/IKE-01-A/posts" && method === "GET") return route.fulfill({ json: [] });
    if (path === "/api/v1/community-spaces/IKE-01-A/membership" && method === "GET") {
      return route.fulfill({ json: { community_code: "IKE-01-A", is_member: false, joined_at: null } });
    }
    if (path === "/api/v1/community-spaces/IKE-01-A/membership" && method === "POST") {
      return route.fulfill({ json: { community_code: "IKE-01-A", is_member: true, joined_at: "2026-11-24T12:00:00Z" } });
    }
    return route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/login");
  await page.getByLabel("Email address").fill("citizen@example.test");
  await page.getByLabel("Password").fill("StrongTestPassword123");
  await page.getByRole("button", { name: /Sign in to GovConnect/ }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByRole("link", { name: "Community Connect" }).click();
  await page.getByLabel("State").selectOption("LA");
  await page.getByLabel("Local Government Area").selectOption("IKE");
  await page.getByLabel("Ward").selectOption("IKE-01");
  await page.getByLabel("Community").selectOption("IKE-01-A");
  await page.getByRole("button", { name: "Join community" }).click();
  await expect(page.getByLabel("Share an update")).toBeVisible();
});
