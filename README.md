# GovConnect Nigeria

GovConnect Nigeria is a citizen-reporting application with a **Python FastAPI backend** and a **JavaScript/TypeScript React frontend** in one repository. The frontend and backend run as separate local processes but communicate through the versioned HTTP API; there is no need to rewrite the backend in JavaScript.

## Application structure

- `backend/` — FastAPI API, SQLAlchemy models, authentication, report workflow, notifications, SLA tracking, and private evidence attachments.
- `frontend/` — React + TypeScript + Vite browser application.
- `.github/workflows/` — backend tests and frontend build checks.

## API contracts

Authentication: `POST /api/v1/auth/register` (email, full_name, password), `POST /api/v1/auth/login` (email, password), and `GET /api/v1/auth/me`. Login returns `access_token`, `token_type`, and `user`; send the token as `Authorization: Bearer <token>`.

Reports: `POST /api/v1/reports`, `GET /api/v1/reports`, `GET /api/v1/reports/{report_id}`. Evidence endpoints support authenticated upload/list/download at `/api/v1/reports/{report_id}/attachments`. The API also provides department assignment, status history/comments, notifications, and SLA summaries. Explore `http://localhost:8000/docs` while the API is running.

Public registration always creates a citizen. Roles are citizen, official, department_admin, supervisor, and system_admin. Backend authorization is authoritative; frontend visibility is not a security boundary. Passwords use PBKDF2-HMAC-SHA256; access tokens are signed JWTs with a 30-minute default expiry.

## Local development

Requirements: Python 3.12+ and Node.js 22+.

### Start the backend

Linux/macOS:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp ../.env.example .env
python -m uvicorn app.main:app --reload
```

Windows PowerShell:
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Set a strong random `JWT_SECRET` before deployment. `CORS_ORIGINS` is a comma-separated allowlist; defaults permit the local Vite origins on port 5173.

### Start the frontend (second terminal)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. `VITE_API_URL` is the backend origin only (default `http://localhost:8000`); the client adds `/api/v1`.

### Checks

Backend, from `backend/`: `python -m unittest discover -s tests -v`.
Frontend, from `frontend/`: `npm install && npm run build`.

## Frontend foundation

The initial connected UI includes citizen registration/login, session restoration via `GET /auth/me`, protected routes, sign-out, a citizen dashboard, report counts/list, and a report submission form with coordinates. Evidence upload UI, report detail/history, official/department dashboards, notification/SLA views, and production deployment are follow-on work.

## Security and production notes

The initial browser client stores the short-lived bearer token in localStorage because the API does not yet implement an HttpOnly refresh-cookie flow. This is an interim trade-off and is exposed to token theft if an XSS vulnerability is introduced. Keep dependencies current, avoid unsafe HTML rendering, and plan a hardened refresh/session design before public production. Never put secrets in frontend environment variables; Vite variables are bundled into browser code.

Evidence files currently use local filesystem storage. Production needs durable private storage outside the web root, backups, and malware scanning. Other gaps include rate limiting, email verification/account recovery, audit logs, monitoring, HTTPS, production database, and managed migrations.

See [GOVCONNECT_PROGRESS.md](GOVCONNECT_PROGRESS.md) for phase history and the current development checkpoint.


## Current development checkpoint — 4 November 2026

- Existing System Admin Command Centre work remains on `feature/admin-command-centre-phase-9` and PR #7 remains open.
- Follow-up implementation is on `feature/admin-oversight-enforcement-phase-10`, based on the existing admin branch. Do not commit directly to `main`.
- Phase 10 currently adds an admin-only reporting oversight API and dashboard panel for high reporting volume, 24-hour submission bursts and repeated report content.
- These are human-review indicators only, not findings of false reporting and not automatic grounds for penalties.
- Backend API tests were added. GitHub Actions backend tests and frontend dependency audit/typecheck/build passed on PR head `e399fa6`; manual browser regression is still pending.
- Next: validate this branch, then continue with user management, report enforcement, notifications and immutable admin audit logs.
- Resume commands:
  ```powershell
  cd C:\\Users\\gentle\\govconnectx
  git fetch origin
  git switch feature/admin-oversight-enforcement-phase-10
  git pull --ff-only origin feature/admin-oversight-enforcement-phase-10
  ```

See [GOVCONNECT_PROGRESS.md](GOVCONNECT_PROGRESS.md) and [docs/ADMIN_COMMAND_CENTRE_HANDOFF.md](docs/ADMIN_COMMAND_CENTRE_HANDOFF.md) for detailed handoff notes.


## Current development checkpoint — 4 November 2026 (Phase 11)

- Public experience refresh is on `feature/public-home-theme-login-phase-11`, stacked on `feature/admin-oversight-enforcement-phase-10`.
- Added a public landing page at `/` with clear sign-in and registration calls to action.
- Added a persistent light/dark theme toggle shared by the landing page, sign-in, registration and authenticated application shell.
- Updated typography to Nunito Sans and Plus Jakarta Sans and refreshed the sign-in layout.
- Existing login API, role-based authorization, citizen dashboard and System Admin Command Centre routes remain unchanged.
- PR #9: https://github.com/cikwom/govconnectx/pull/9 (open; not merged).
- Next: run frontend CI/build, pull this branch locally, refresh `http://localhost:5173/`, test both themes and sign in. Then review PR #9 before merge.
- Resume commands:
  ```powershell
  cd C:\\Users\\gentle\\govconnectx
  git fetch origin
  git switch feature/public-home-theme-login-phase-11
  git pull --ff-only origin feature/public-home-theme-login-phase-11
  ```


## Current development checkpoint — Nigerian legal pages

**Date:** 9 November 2026  
**Branch:** `feature/nigerian-legal-pages-privacy-terms`

- Added public Terms of Use and Privacy Notice routes at `/terms` and `/privacy`.
- Added legal links to the public landing page and authenticated application footer.
- Registration now requires users to acknowledge the Terms of Use and confirm they have read the Privacy Notice before submitting the form.
- Legal-page wording is grounded in the current app's account, report, attachment, authentication, and storage implementation, and references the Nigeria Data Protection Act 2023.
- The pages deliberately disclose unresolved launch requirements: operator legal identity and contact, privacy-request channel, retention schedule, actual hosting/service-provider locations, durable database and private attachment storage, backups, and legal review.
- GovConnect is not described as a government agency or as an endorsed government service without formal authorisation.
- Database-provider setup remains deferred; this UI/legal work does not require Neon.
- **Next:** run frontend build and backend tests, review legal wording with a qualified Nigerian privacy lawyer, supply the operator's legal name/address and privacy contact, then merge the PR only after CI passes.


## Current development checkpoint — Phase 1 security hardening

**Date:** 9 November 2026  
**Branch:** `feature/production-database-safety-phase-1`

- Started Phase 1 on a feature branch from the verified `main` commit `a8e5bb04ebdb0c7fbaa4352cf9900a63e9ec9e2b`; no direct commits to `main`.
- First security change: `backend/app/database.py` now rejects SQLite when `ENVIRONMENT=production`, preventing an absent or misconfigured `DATABASE_URL` from silently starting the hosted app against a local SQLite file.
- Local development and test environments retain the existing SQLite fallback.
- Commit: `533a9fb3084239b2655d051890624ff4567a6a37` — `fix(security): reject SQLite database in production`.
- Tests for the configuration guard are the next step; this commit has not yet been validated by CI.
- Next: add unit coverage for production rejection and local/test SQLite behaviour, then continue with authentication abuse protection and audit logging.
