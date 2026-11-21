# GovConnectX

GovConnectX is a civic reporting and public-service coordination platform for Nigeria. It connects citizens, government departments, agency staff and system administrators through geographically organised report workflows and accountability tools.

## Repository

- `backend/` — Python FastAPI API, SQLAlchemy models, authentication, authorization, report workflows and integrations.
- `frontend/` — React, TypeScript and Vite application.
- `.github/workflows/` — automated backend, frontend and browser checks.
- `docs/testing/` — regression checklists, release gates and dated test evidence.

## Current status — 21 November 2026

**Verified main commit:** `0b2bc05491194998e23aa2cd293fee43a4b697ea` (PR #74 merge).

PR #74 completed secure staff invitations and onboarding for official, supervisor and department-admin roles. Invitations use expiring, single-use tokens stored as SHA-256 digests, support revocation and department/geographic scope, and generate audit events.

Implemented areas include citizen registration and reporting; Nigerian geopolitical-zone, State/LGA and local geography; department scopes and report routing; evidence workflows; admin oversight and audit events; transparency; citizen services; multilingual UI; accessibility foundations; agency and field-officer workflows; private staff notes; staff assignment; and secure staff onboarding.

## Local development

Requirements: Python 3.12+ and Node.js 22+.

Backend setup (Windows PowerShell): from the repository root run `py -3.12 -m venv backend\.venv`, then `backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`. Copy `.env.example` to `backend\.env` and configure local values.

Start the API from `backend/` with `python -m uvicorn app.main:app --reload`. API docs: http://127.0.0.1:8000/docs.

Frontend: open a second terminal, run `cd frontend`, `npm.cmd ci`, then `npm.cmd run dev`. Open http://localhost:5173; sign-in is at http://localhost:5173/login. Use `npm.cmd` if PowerShell blocks `npm.ps1`.

## Automated checks

Backend: from `backend/`, run `python -m unittest discover -s tests -v`.

Frontend: from `frontend/`, run `npm.cmd ci`, `npm.cmd run check:translations`, `npm.cmd run check:accessibility`, `npm.cmd run typecheck`, and `npm.cmd run build`.

Browser suite: from `frontend/`, run `npm.cmd run test:e2e` after installing Playwright Chromium as described in `docs/testing/README.md`.

Latest verified post-merge baseline: full CI passed, backend suite passed (104 tests), frontend build passed and Playwright Chromium suite passed (10 tests). Browser tests use mocked API fixtures and do not prove live-backend or production integration.

## Production readiness

Do not enable public production evidence uploads until private durable object storage, malware scanning/quarantine, access controls, backup/restore, quotas, retention/deletion and audit requirements are configured and tested.

Before launch, verify managed PostgreSQL and migrations, strong secrets, HTTPS, exact CORS allowlists, rate limiting, SMTP and SMS provider delivery, worker/retry operations, monitoring, backups and a successful restoration drill. Complete API authorization/security review, privacy and retention review, manual accessibility testing and native-speaker translation review.

Frontend session hardening, legal operator/contact details and qualified Nigerian privacy/legal review also remain release considerations. GovConnectX must not be represented as a government agency or endorsed government service without formal authorisation.

## Project records

- [Development checkpoint](GOVCONNECT_PROGRESS.md)
- [Testing hub](docs/testing/README.md)
- [Manual regression checklist](docs/testing/MANUAL_REGRESSION_CHECKLIST.md)
- [Pull request and release gate](docs/testing/RELEASE_GATE.md)
- [Test evidence log](docs/testing/TEST_EVIDENCE.md)
- [Geographical zones handoff](docs/GEOGRAPHICAL_ZONES_HANDOFF.md)
- [Accountability engine handoff](docs/ACCOUNTABILITY_ENGINE_HANDOFF.md)
- [Citizen services handoff](docs/CITIZEN_SERVICES_HANDOFF.md)

## Next work

Bring the historical handoff notes and test evidence fully up to date, run live-backend integration tests, then close production storage/recovery, notification delivery, security, privacy and accessibility release gaps. A green CI run is not by itself a production-readiness sign-off.

- [Deferred production-readiness backlog](docs/PRODUCTION_READINESS_BACKLOG.md)
