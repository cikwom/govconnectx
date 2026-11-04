# System Admin Command Centre — Handoff

## Purpose
Provide the GovConnectX System Admin with a protected operational view of platform users, citizen reports and recorded activity, then extend it with reviewable reporting-pattern indicators and carefully controlled enforcement workflows.

## Existing Command Centre endpoints
- `GET /api/v1/admin/overview` — user counts, role counts, report status counts, open and overdue totals.
- `GET /api/v1/admin/users` — searchable/paginated directory with account state and number of reports submitted.
- `GET /api/v1/admin/reports` — searchable report list including reporter name/email and report description.
- `GET /api/v1/admin/activity` — recent account registrations, report status events and assignments.

## Phase 10 — Advanced reporting oversight
- `GET /api/v1/admin/oversight` — System Admin-only review signals based on report data in a configurable time window.
- Query parameters: `window_days` (1–365, default 30), `min_reports` (2–50, default 5), `burst_threshold` (2–20, default 4), and `limit` (1–100, default 50).
- Signals currently include high reporting volume, a short submission burst (rolling 24-hour window), and repeated identical category/title/description content by the same citizen.
- The dashboard shows review priority, signal explanations and the related reports.
- No new database table or schema migration is required for this analytics-only phase; signals are calculated from existing report records.

### Important interpretation and safety rules
- A signal is an indicator for human review, not proof of false reporting, fraud, abuse or wrongdoing.
- The system does not automatically warn, suspend, block, reject or otherwise penalize a citizen based on these signals.
- A citizen may legitimately submit many reports, and duplicate text may reflect repeated incidents. Admins must inspect context and evidence before making a finding.
- The current report schema has no verified-false-report outcome. Do not label users as repeat offenders until a human-reviewed finding and its supporting evidence are recorded in a later enforcement phase.
- Oversight is limited to data users submitted or actions recorded inside GovConnectX; it does not inspect private messages, keystrokes or off-platform activity.

## Authorization and privacy
All admin endpoints use `require_roles("system_admin")`. Backend authorization is authoritative; hiding the navigation link is not a security boundary. User responses are explicitly shaped and do not include password hashes or credentials.

## Remaining phases
1. User Management — warnings, temporary suspension, blocking and reinstatement with reason, duration, actor and appeal/review safeguards.
2. Report Enforcement — report investigation, evidence review, verified outcomes and reasoned decisions.
3. Notification Centre — in-app notices for warnings and account/report decisions.
4. Audit Logs — append-only administrative action history, including actor, target, action, reason, timestamp and reversal metadata.

These phases should build on the existing users, reports, report history and notifications architecture. Do not create a parallel administration subsystem.

## Verification still required
- Run backend unit/API tests and frontend typecheck/build.
- Verify citizens receive HTTP 403 from `/api/v1/admin/oversight`.
- Verify the admin dashboard renders the review panel and that no-signal results are handled.
- Verify window and threshold validation, burst boundaries and repeated-content detection.
- Complete manual browser regression and review CI before merging.
