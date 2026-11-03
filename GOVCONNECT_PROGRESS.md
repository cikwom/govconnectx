# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Current feature branch:** `feature/citizen-report-details-evidence-phase-6`  
**Checkpoint:** 4 November 2026

## Product direction

GovConnectX should be powerful behind the scenes and simple for citizens:
- Keep login and registration clear, uncluttered and mobile-friendly.
- After login, make the main actions obvious: **Report an issue**, **My reports / Track progress**, **Lost something**, **Found something**, and **Get help**.
- Avoid exposing staff workflows, department administration, SLA jargon or complex navigation to ordinary citizens.
- Make issue reporting short: category, description, location, optional photo, submit; then show a reference and tracking link.
- Lost & Found is a separate module from government complaints. It should support reports across all Nigerian states, possible-match suggestions, private communication, ownership verification and safe handover. Never publish sensitive item details, document numbers, home addresses or private contact details.

## Repository and PR status

- `main` last verified at `f9c75a3a5875f5ab0ade0f364982a27f9fd438d9`.
- Phases 1–5 are merged (PRs #1–#5).
- Phase 6 is [PR #6](https://github.com/cikwom/govconnectx/pull/6), open and not merged.
- Phase 6 branch: `feature/citizen-report-details-evidence-phase-6`; latest known head before this product-planning update: `6ae14c7f9382e49605ce9102f2b5d0efb1730bc6`.
- PR #6 was reported mergeable. Recheck CI on the latest head before merge.
- `main` is not protected; configure branch protection/status checks if repository permissions allow.
- Do not claim work is merged until GitHub confirms it and main advances.

## Completed phases

- **Phase 1:** citizen registration/login, PBKDF2 password hashing, JWT, RBAC, admin bootstrap, backend CI.
- **Phase 2:** departments/staff, report assignment, status workflow/history, public comments and internal notes.
- **Phase 3:** in-app notifications and configurable SLA tracking.
- **Phase 4:** authenticated JPEG/PNG/PDF evidence upload/list/download, signature validation, 10 MiB default cap, private local storage.
- **Phase 5:** React + TypeScript + Vite frontend, auth/session restoration, protected routes, citizen dashboard/report submission, FastAPI CORS and frontend CI.

## Phase 6 — citizen report details and evidence (PR #6)

Implemented:
- Report detail route/page and dashboard links.
- Public status history and comments; citizen public comment submission.
- Evidence listing, JPEG/PNG/PDF upload and authenticated downloads.
- Improved temporary download URL cleanup.

Latest CI previously verified on commit `6ae14c7f9382e49605ce9102f2b5d0efb1730bc6`:
- Frontend dependency audit, typecheck and build: **PASS**, run 41735481886.
- Backend tests: **PASS**, run 41735482129.
- Manual browser testing: **NOT RUN**. Run checklist sections A, C, D and E before merging.
- PR #6 remains open for owner review/merge.

## Permanent testing documentation

- `docs/testing/README.md` — testing hub and commands.
- `docs/testing/MANUAL_REGRESSION_CHECKLIST.md` — repeatable end-to-end checks across roles and features.
- `docs/testing/RELEASE_GATE.md` — merge and production release gates.
- `docs/testing/TEST_EVIDENCE.md` — dated evidence; Phase 6 manual browser run remains pending.

Record exact branch and commit SHA for every test. Never mark a test passed until it has actually run.

## Roadmap — planned, not yet implemented

1. **Phase 7 — Simple citizen experience:** simplify login/registration and citizen home; make report issue, my reports/track, lost/found and get help obvious; make report submission short and mobile-first. Keep staff/admin navigation separate and role-aware.
2. **Phase 8 — Nationwide Lost & Found:** lost and found listings; structured item/category/location/date details; cross-state search; safe possible-match suggestions; private in-app contact; proof-of-ownership workflow; safe handover and item-return closure; abuse/scam reporting and moderation. Do not publicly expose sensitive details or private contact information.
3. **Phase 9 — Official and department dashboards:** role-specific queues, department filters, report assignment UI, staff status actions, permission-aware report views.
4. **Phase 10 — Notifications and SLA frontend:** notification inbox, unread/read actions, SLA summary and due-soon/overdue indicators.
5. **Phase 11 — Administration and governance:** staff/department management, user administration, audit trail and operational configuration.
6. **Phase 12 — Production hardening:** secure session/refresh strategy, rate limiting, email verification/account recovery, durable private object storage, malware scanning, migrations, backups/restore, monitoring, HTTPS and deployment runbook.
7. **Phase 13 — Final QA and release:** full regression, accessibility/usability, security review, performance checks, deployment rehearsal and release sign-off.

Start Phase 7 from latest main after PR #6 is merged. Start each subsequent phase from the latest merged main; do not stack long-running phases on unmerged branches.

## Outstanding work

- Owner reviews and merges PR #6.
- Run and record Phase 6 manual browser tests.
- Build Phase 7 simple citizen UX and verify mobile usability/accessibility.
- Build Phase 8 nationwide Lost & Found with privacy, verification and abuse prevention.
- Configure main branch protection/status checks if possible.
- Complete remaining roadmap phases.
- Replace local-only evidence storage before production.
- Complete production security, migrations, backup/restore, monitoring and deployment review before accepting real citizen data.

## Resume commands

```bash
git fetch origin
git switch feature/citizen-report-details-evidence-phase-6
git pull --ff-only origin feature/citizen-report-details-evidence-phase-6

# Backend terminal
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend terminal
cd frontend
npm ci
npm run dev
```

Frontend: `http://localhost:5173` · API docs: `http://localhost:8000/docs`.

Testing hub: [docs/testing/README.md](docs/testing/README.md).