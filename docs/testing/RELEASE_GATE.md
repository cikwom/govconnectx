# Pull request and release gate

Use this before merging each feature PR. A green build is necessary but does not replace security review or browser testing.

## Pull request gate

- [ ] PR targets the intended base branch and is limited to the described phase.
- [ ] No uncommitted/unpushed work is left locally; the PR head matches the tested commit.
- [ ] Backend test workflow passes on the latest PR head.
- [ ] Frontend typecheck/build workflow passes on the latest PR head.
- [ ] Dependency audit/security workflow passes where configured; findings are reviewed, not blindly ignored.
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

## Current known release blockers

- Manual end-to-end browser checks for Phase 6 have not yet been recorded.
- Evidence files currently use local filesystem storage; production needs durable private storage and backups.
- Frontend bearer token currently uses localStorage; a hardened refresh/session design remains planned.
- Production database migration strategy, backups/restore, monitoring, rate limiting, HTTPS and audit logging need completion.
- Main branch currently has no protection rules; require PR reviews/status checks if repository permissions allow.
