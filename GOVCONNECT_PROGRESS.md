# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Current feature branch:** `feature/citizen-report-details-evidence-phase-6`  
**Checkpoint date:** 3 November 2026

## Repository and PR status (verified)

- `main` is at `f9c75a3a5875f5ab0ade0f364982a27f9fd438d9`.
- Phases 1–5 are merged (PRs #1–#5).
- Phase 6 is in [PR #6](https://github.com/cikwom/govconnectx/pull/6), currently open and not merged.
- Phase 6 branch head at this checkpoint: `8704aefbff6a43bfb03760c6183319ce0749de3f`.
- PR #6 is reported mergeable. Do not mark it merged until GitHub reports merged and main advances.
- All 7 currently listed branches are known historical/feature branches; only PR #6 is open among the recent PRs checked.
- `main` is not protected. Configure protection/status checks in GitHub Settings when repository permissions permit.

## Completed phases

- **Phase 1:** citizen registration/login, PBKDF2 password hashing, JWT, RBAC, admin bootstrap, backend CI.
- **Phase 2:** departments/staff, report assignment, status workflow/history, public comments and internal notes.
- **Phase 3:** in-app notifications and configurable SLA tracking.
- **Phase 4:** authenticated JPEG/PNG/PDF evidence upload/list/download, signature validation, 10 MiB default cap, private local storage.
- **Phase 5:** React + TypeScript + Vite frontend, auth/session restoration, protected routes, citizen dashboard/report submission, FastAPI CORS and frontend CI.

## Phase 6 — citizen report details and evidence (PR #6)

Implemented on `feature/citizen-report-details-evidence-phase-6`:
- Report detail route/page and dashboard links.
- Public status history and comments; citizen public comment submission.
- Evidence listing, JPEG/PNG/PDF upload, authenticated downloads.
- Download URL cleanup delayed briefly after the browser download starts.

Latest verified CI on exact head `8704aefbff6a43bfb03760c6183319ce0749de3f`:
- Frontend build/typecheck/dependency audit: **PASS**, run 41717048388.
- Backend tests: **PASS**, run 41717048474.
- Manual browser checks: **NOT RUN**. The owner should run `docs/testing/MANUAL_REGRESSION_CHECKLIST.md` sections A, C, D and E before merging.
- PR #6 remains open for owner review/merge.

## Permanent testing documentation

- `docs/testing/README.md` — testing hub and commands.
- `docs/testing/MANUAL_REGRESSION_CHECKLIST.md` — repeatable end-to-end checks across roles and features.
- `docs/testing/RELEASE_GATE.md` — merge and production release gates.
- `docs/testing/TEST_EVIDENCE.md` — dated test evidence; manual Phase 6 run remains pending.

Record the exact branch and commit SHA for every run. Do not mark manual checks passed until executed.

## Next development phases (planned, not yet implemented)

1. **Phase 7 — Official and department dashboards:** role-specific queues, department filters, report assignment UI, staff status actions, and permission-aware report views.
2. **Phase 8 — Notifications and SLA frontend:** notification inbox, unread count/read actions, SLA summary, due-soon/overdue indicators.
3. **Phase 9 — Administration and governance:** staff/department management, user administration, audit trail, operational configuration and admin UI.
4. **Phase 10 — Production hardening:** secure session/refresh strategy, rate limiting, email verification/account recovery, durable private object storage, malware scanning, migrations, backups/restore, monitoring, HTTPS and deployment runbook.
5. **Phase 11 — Final QA and release:** full regression, accessibility/usability, security review, performance checks, deployment rehearsal and release sign-off.

Phase 7 should begin from the latest main after PR #6 is merged, to avoid building on a temporary stacked branch.

## Outstanding project-wide work

- Run Phase 6 manual browser checks and record results.
- Review and merge PR #6 (owner action).
- Configure main branch protection and require CI checks if permissions allow.
- Build and test Phases 7–11 above.
- Replace local-only evidence storage before production.
- Implement production session hardening, rate limiting, email verification/account recovery, audit logs, database migrations, backup/restore and monitoring.
- Complete deployment and security review before real citizen data is accepted.

## Resume commands

```bash
git fetch origin
git switch feature/citizen-report-details-evidence-phase-6
git pull --ff-only origin feature/citizen-report-details-evidence-phase-6

# Terminal 1 — backend
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm ci
npm run dev
```

Frontend: `http://localhost:5173` · API docs: `http://localhost:8000/docs`.

Testing hub: [docs/testing/README.md](docs/testing/README.md). Start with [the manual regression checklist](docs/testing/MANUAL_REGRESSION_CHECKLIST.md).