# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Working branch:** `feature/frontend-foundation-phase-5`  
**Checkpoint date:** 3 November 2026

## Current Git status

- Phase 1 authentication/RBAC, Phase 2 report workflow, Phase 3 notifications/SLA, and Phase 4 secure evidence attachments are merged.
- Phase 4 merge commit: `23b1f364f8a1fe37a37ae83f523371322705e154`.
- Phase 5 frontend foundation is on `feature/frontend-foundation-phase-5`; use a PR and do not push directly to `main`.
- `main` was reported unprotected at the last settings check; do not assume branch protection is enabled.

## Completed phases

- **Phase 1:** citizen registration/login, PBKDF2 password hashing, JWT, role-based access, bootstrap system administrator, backend CI.
- **Phase 2:** departments/staff assignment, report assignment, validated status history, public comments and staff-only notes.
- **Phase 3:** in-app notification inbox/read actions, notifications on report changes, configurable 72-hour default SLA and role-scoped summary.
- **Phase 4:** authenticated JPEG/PNG/PDF evidence upload/list/download, signature/extension validation, 10 MiB default cap, private local storage, authorization and attachment tests.

## Phase 5 — frontend foundation and API integration

Implemented on this branch:
- Added a React 18 + TypeScript + Vite frontend under `frontend/` in the same repository.
- Added typed API client for the real auth and report API contracts.
- Added registration, login, auth context, session restoration through `GET /auth/me`, protected routes, and sign-out.
- Added citizen dashboard with report counts/list and a report submission form requiring coordinates.
- Added configurable FastAPI CORS allowlist (default local Vite origins).
- Added frontend build/type-check workflow and updated root setup documentation.
- Token persistence currently uses localStorage to work with the existing bearer-token API; this is an interim security trade-off, not the final production session architecture.

## Verification and next work

- Confirm latest PR-head backend tests and frontend build/type-check pass in GitHub Actions.
- Local backend: from `backend/`, run `python -m unittest discover -s tests -v` and `python -m uvicorn app.main:app --reload`.
- Local frontend: from `frontend/`, run `npm install && npm run build && npm run dev`.
- Verify registration/login and report create/list against the local API.
- Set production `CORS_ORIGINS` to exact deployed frontend origins; never use wildcard origins.
- Next: evidence upload/download UI, report detail/history, official/department dashboards, notification/SLA views, system-admin UI.

## Production backlog

Strong JWT secret, HTTPS, production database/backups/monitoring, rate limiting, email verification/account recovery, refresh-token/session strategy, privileged audit logs, durable private object storage, malware scanning, Alembic migrations, and verified main-branch protection.

## Resume commands

```bash
git fetch origin
git switch feature/frontend-foundation-phase-5
git pull --ff-only origin feature/frontend-foundation-phase-5
# Terminal 1
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
# Terminal 2
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173` · API docs: `http://localhost:8000/docs`. Review CI and the PR diff before merging Phase 5.
