# GovConnectX — Production Readiness Backlog

**Created:** 21 November 2026  
**Status:** Deferred follow-up work — track and complete in dedicated implementation phases  
**Current baseline:** `main` at `0b2bc05491194998e23aa2cd293fee43a4b697ea` (PR #74)

This file deliberately separates production-readiness work from the current documentation checkpoint. The items below are not claimed to be completed merely because automated CI is green.

## Priority 1 — Production infrastructure and recovery

- [ ] Select and configure managed PostgreSQL for the target deployment.
- [ ] Verify schema migrations, migration ordering, rollback/recovery procedure and connection security.
- [ ] Configure private, durable object storage for report evidence; enforce least-privilege access and signed/controlled retrieval.
- [ ] Integrate and verify real malware scanning, quarantine and safe failure behavior for uploaded evidence.
- [ ] Define file size/type limits, quotas, retention, deletion and audit requirements.
- [ ] Configure automated database and media backups.
- [ ] Perform and document a successful restoration drill, including media-to-record consistency.
- [ ] Add production health monitoring, alerting, logs and incident/rollback procedures.

## Priority 2 — Real email and SMS delivery

- [ ] Configure production SMTP credentials and sender/domain verification.
- [ ] Configure the SMS provider (Termii or approved alternative) and validate consent enforcement before every send.
- [ ] Deploy and supervise a separate notification worker.
- [ ] Implement provider delivery receipts/webhooks and reconcile delivery states.
- [ ] Classify transient versus permanent failures and implement bounded retries/backoff.
- [ ] Provide administrator review and safe replay for dead-letter notifications.
- [ ] Test opt-out, consent withdrawal, duplicate prevention, rate limits and provider outage behavior.
- [ ] Verify templates and delivery behavior for English, Hausa, Yorùbá and Igbo.

## Priority 3 — Security, privacy and governance

- [ ] Review frontend token/session storage and harden session lifecycle, expiry and logout.
- [ ] Run API authorization tests across citizen, official, supervisor, department-admin, field-officer and system-admin roles.
- [ ] Test cross-department and cross-geography access denial, including direct object-ID access.
- [ ] Complete external security/penetration testing and remediate findings.
- [ ] Verify HTTPS, production secrets, exact CORS allowlists, rate limits and secure headers.
- [ ] Define data retention/deletion schedules for accounts, reports, evidence, notifications and audit records.
- [ ] Complete privacy impact and data-flow review; document processors and incident response.
- [ ] Obtain qualified Nigerian privacy/legal review and confirm operator identity, privacy contact and lawful authority to use any official identity or branding.
- [ ] Verify repository branch protection and required status checks.

## Priority 4 — Accessibility, localization and geographic data

- [ ] Perform keyboard-only testing of citizen, staff and admin workflows.
- [ ] Test with screen readers on supported desktop and mobile combinations.
- [ ] Test 200% and 400% zoom, narrow viewports, contrast and forced-colors modes.
- [ ] Complete native-speaker review of Hausa, Yorùbá and Igbo translations, including pluralization and form validation.
- [ ] Validate authoritative State, LGA, Ward and Community datasets and record provenance/update ownership.
- [ ] Verify jurisdiction assignment and report routing with representative real-world test locations.
- [ ] Test reports submitted outside a user's home jurisdiction and verify correct triage/permissions.

## Priority 5 — Live acceptance and operational readiness

- [ ] Run live-backend end-to-end tests with a disposable test database and test identities.
- [ ] Cover registration, login, report submission, evidence upload, comments, routing, assignment, staff invitations, account enforcement and audit history.
- [ ] Exercise notification provider success, retry, permanent failure and outage paths.
- [ ] Test concurrent actions, duplicate submissions, idempotency and recovery after worker/API restart.
- [ ] Complete mobile browser regression on supported devices.
- [ ] Prepare deployment, rollback, backup restoration and incident runbooks.
- [ ] Obtain explicit release sign-off; do not describe the system as production-ready until all launch-critical checks are evidenced.

## Current verified automated baseline

The repository audit recorded the following post-merge results for PR #74:

- Full CI: [workflow run 44642161410](https://github.com/cikwom/govconnectx/actions/runs/44642161410) — passed.
- Backend tests: [workflow run 44642161493](https://github.com/cikwom/govconnectx/actions/runs/44642161493) — 104 tests passed.
- Frontend build: [workflow run 44642161784](https://github.com/cikwom/govconnectx/actions/runs/44642161784) — passed.
- Playwright Chromium suite: 10 tests passed.

**Important limitation:** Playwright currently uses mocked API fixtures. These results do not establish live-backend persistence, real provider delivery, production storage, security penetration coverage or manual accessibility acceptance.

## Suggested execution order

1. Live-backend integration baseline and test data.
2. Database, private evidence storage, malware scanning and backup/restore.
3. Email/SMS workers, receipts, retry and dead-letter operations.
4. Security/privacy review and remediation.
5. Manual accessibility, localization and geography acceptance.
6. Production runbooks and release sign-off.

Update this file as each item is implemented and attach links to pull requests, workflow runs, test reports or restoration evidence. Keep unfinished items checked as open; never mark them complete based only on design documentation.
