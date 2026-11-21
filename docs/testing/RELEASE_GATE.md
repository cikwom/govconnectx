# Pull request and release gate

Use this before merging each feature PR. A green build is necessary but does not replace security review or browser testing.

## Pull request gate

- [ ] PR targets the intended base branch and is limited to the described phase.
- [ ] No uncommitted/unpushed work is left locally; the PR head matches the tested commit.
- [ ] Backend test workflow passes on the latest PR head.
- [ ] Frontend typecheck/build workflow passes on the latest PR head, including Playwright browser tests where configured.
- [ ] Production dependencies pass the high-severity audit; the full build-tool dependency tree is audited at critical severity until upstream publishes a fix for the newly disclosed unfixed picomatch advisory. Review and track all findings rather than blindly ignoring them.
- [ ] Database compatibility/migration tests pass where models or schema change.
- [ ] Authorization tests cover both allowed and denied roles/resources.
- [ ] API request/response contracts match frontend types and usage.
- [ ] Manual regression checklist sections affected by the change have been run.
- [ ] No secrets, personal data, local databases, uploaded evidence or build artifacts are committed.
- [ ] Documentation and `GOVCONNECT_PROGRESS.md` are updated.
- [ ] PR description records scope, validation, known gaps and deployment/configuration changes.

## Release gate

- [ ] All intended feature PRs are merged; no required feature remains only on a branch.
- [ ] Run the full backend suite and frontend build against the release candidate.
- [ ] Complete the manual regression checklist with a dated evidence record.
- [ ] Verify production environment variables and exact CORS origins.
- [ ] Confirm HTTPS, strong JWT secret, database backups and restore procedure.
- [ ] Confirm persistent private evidence storage, access controls and backup policy.
- [ ] Confirm upload limits and malware-scanning decision before accepting public uploads.
- [ ] Confirm logging/monitoring and an incident/rollback procedure.
- [ ] Verify no test accounts, test-only settings or sample secrets are enabled in production.

## Automated browser coverage\n\nThe frontend CI runs Playwright Chromium checks for citizen registration, sign-in, and report submission with State/LGA/Ward/Community selection. These tests use isolated mocked API fixtures; they do not replace a live-backend/manual production regression run.\n\n## Current known release blockers

- Manual end-to-end browser checks for Phase 6 have not yet been recorded.
- Evidence files currently use local filesystem storage; production needs durable private storage and backups.
- Frontend bearer token currently uses localStorage; a hardened refresh/session design remains planned.
- Production database migration strategy, backups/restore, monitoring, rate limiting, HTTPS and audit logging need completion.
- Main branch currently has no protection rules; require PR reviews/status checks if repository permissions allow.


## Current verified baseline — 21 November 2026

- Main commit: `0b2bc05491194998e23aa2cd293fee43a4b697ea` (PR #74 merge).
- Full CI passed: [run 44642161410](https://github.com/cikwom/govconnectx/actions/runs/44642161410).
- Backend tests passed: [run 44642161493](https://github.com/cikwom/govconnectx/actions/runs/44642161493) — 104 tests.
- Frontend build passed: [run 44642161784](https://github.com/cikwom/govconnectx/actions/runs/44642161784); Playwright Chromium suite: 10 tests.
- Browser tests use mocked API fixtures; live-backend and production integration are not proven by these runs.

## Outstanding release verification

- Live-backend end-to-end regression: NOT RUN.
- Production PostgreSQL, migrations, backup/restore and monitoring: NOT VERIFIED.
- Durable private evidence storage and production malware scanning: NOT VERIFIED; keep production evidence uploads disabled until configured and tested.
- Real SMTP/SMS delivery, receipts, retries, worker and dead-letter operations: NOT VERIFIED.
- Manual mobile, keyboard, screen-reader, zoom, contrast and forced-colors testing: NOT RUN.
- Native-speaker translation review, external security testing and qualified privacy/legal review: NOT RUN.
- Frontend session hardening and production secret/CORS/HTTPS/rate-limit settings require deployment review.
- Branch protection and required status checks must be verified in GitHub settings; do not infer their state from this checklist.
