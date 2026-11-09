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


### Phase 1 checkpoint update — database configuration tests

- Added `backend/tests/test_database_config.py` with five cases: production rejects a missing URL, production rejects SQLite, production accepts a managed database URL, development retains its SQLite fallback, and tests may explicitly use SQLite.
- Test commit: `cdcce8c7aaf0ed62fffd128a6625034f659620bd` — `test(security): cover production database configuration`.
- README checkpoint commit: `7ad3c915a3c1a002ed452200109df230848b8b57`.
- The implementation and tests are pushed to the feature branch through GitHub. CI has not yet been observed for this branch; do not merge until checks pass.


## Current development checkpoint — Geographical zones Phase 1

**Date:** 9 November 2026  
**Branch:** `feature/geographical-zones-phase-1`  
**Base:** PR #16 head `57de33d8a527b7b689057ac3c551e50b40b0f25e` (security PR remains open; this branch is stacked on it).

- Added a reference directory for 37 state-level units (36 states + FCT) and 774 LGAs, including six geopolitical-zone labels.
- Added public State and state-scoped LGA lookup endpoints.
- Added nullable home State/LGA fields to citizen profiles and nullable incident State/LGA fields to reports.
- Added server-side validation that a selected LGA belongs to its selected State.
- Existing users and reports remain compatible because new location fields are nullable.
- Source data attribution and follow-on requirements are documented in `docs/GEOGRAPHICAL_ZONES_HANDOFF.md`.
- Added dependent State/LGA selectors to registration and report submission; citizens select a private home area, while each report independently selects its incident area.
- **Not yet implemented:** staff geographic scopes, geographic report authorization, automatic department routing, and ward-level boundaries. Do not describe this phase as complete zoning-based access control.
- **Validation status:** four additional API tests cover home-area capture, cross-state incident reporting, and invalid State/LGA combinations. The test commit is `423a5b66bbfba8ddd6d16df33f6ce56a2a66a8c4`. CI workflow branch filters were expanded in commit `82ba68b4057bcc3902eff9105bb519d72059b2db`. Frontend selector implementation commit: `8da6cb315071cda937b51242ce19ca4b4e57e140`. Latest CI is running; local tests/browser checks have not been performed from the user's Windows checkout.
- **Next:** run backend unit tests and frontend build; add frontend dependent selectors; then implement staff geographic scopes and enforce them server-side before any zone-specific dashboard is exposed.

Resume commands:
```powershell
cd C:\Users\gentle\govconnectx
git fetch origin
git switch feature/geographical-zones-phase-1
git pull --ff-only origin feature/geographical-zones-phase-1
```


## Current development checkpoint — Photo and video report evidence

**Date:** 9 November 2026  
**Branch:** `feature/report-photo-video-evidence`  
**Base:** `feature/geographical-zones-phase-1` at `30d11510f020ae6db22a4686471242a96a36513f`.

- Extended private report evidence uploads to accept JPEG, PNG, PDF, MP4, WebM, and QuickTime MOV files.
- Added file-signature checks for MP4/QuickTime and WebM rather than trusting the browser-provided MIME type alone.
- Kept image/PDF uploads at 10 MiB by default and set video uploads to 50 MiB by default; both limits are configurable with `REPORT_ATTACHMENT_MAX_BYTES` and `REPORT_VIDEO_MAX_BYTES`.
- Added API tests for MP4/WebM uploads, MIME mismatch rejection, and video size limits.
- Updated report detail UI to allow file selection, mobile camera photo capture, mobile video capture where the browser/device supports it, and clear video attachment labels.
- Added the mobile camera capture controls in commit `24cf575470f530286852d713537a15f9e19c4ce2`; the browser/device decides whether to open its camera interface or provide another supported capture option.
- **Important deployment limitation:** evidence is still stored on the backend local filesystem. Render's ephemeral filesystem is not durable storage; this is suitable for local development only until private object storage, backups, malware scanning, and retention controls are configured. Do not treat uploaded evidence as safely retained in production yet.
- **Not yet implemented:** staff geographic scopes, backend geographic access enforcement, automatic LGA/department routing, and map-based incident pin verification. The current location selectors allow citizens to choose any State/LGA, independently of home area.
- **Validation:** commit `ef1ad4fdada99012052691a66a96fd20ad24d16d` adds the upload/UI/tests/docs; commit `ebde5761e778481069715b0d44fd84eb6ad91d4f` corrects video signature test fixtures and enables workflow filters for this stacked PR. The push-triggered backend suite and frontend build both passed; PR-triggered checks were still running at checkpoint time. Local Windows/browser tests remain pending.

Resume:
```powershell
cd C:\Users\gentle\govconnectx
git fetch origin
git switch feature/report-photo-video-evidence
git pull --ff-only origin feature/report-photo-video-evidence
```



## Current development checkpoint — production-safe report evidence

**Date:** 9 November 2026  
**Branch:** `feature/report-photo-video-evidence`

- Merged PR #16 (production database safety) into `main` with merge commit `a1e04ed39e3d85b40f2edfd5f8e1bc9f4052988b`.
- Merged PR #17 (Nigerian state/LGA directory and incident geography) into `main` with merge commit `c47ab7d1d8f9ed02ab05743035fbe726f7b0b9fe`.
- PR #18 was retargeted to `main`; its original feature work remains on `feature/report-photo-video-evidence`.
- Added a production safety guard: report evidence uploads return HTTP 503 while `ENVIRONMENT=production`, because the current implementation uses local filesystem storage and Render's default filesystem is ephemeral.
- Added a regression test proving production uploads stay disabled. Local development and tests continue to exercise image/video upload behaviour.
- Evidence uploads must remain disabled in production until private durable object storage, malware scanning/quarantine, backup/restore, quotas, retention/deletion and access auditing are implemented and configured.
- **Validation:** the new production guard and regression test are committed in this checkpoint; GitHub Actions must pass on the updated PR head before PR #18 is merged.
- **Next:** wait for backend and frontend CI on the updated PR #18 head; then merge only if checks pass and mergeability is confirmed. Pull the merged `main` branch locally and test the application. Do not claim that production media upload is enabled.

Resume commands:
```powershell
cd C:\Users\gentle\govconnectx
git fetch origin
git switch feature/report-photo-video-evidence
git pull --ff-only origin feature/report-photo-video-evidence
```


## Current development checkpoint — Geographical Zones Phase 2

**Date:** 9 November 2026  
**Branch:** `feature/geographical-zones-phase-2`  
**Base:** `main`, including merge commit `9b19e412298c6804fa1e262d0010ac72f88784ff` (PR #18).

- PR #16 (production database safety), PR #17 (Nigeria's 37 state-level units and 774 LGAs), and PR #18 (private photo/video evidence support) are merged into `main`.
- PR #18 adds JPEG/PNG/PDF and MP4/WebM/MOV evidence support, mobile capture controls, signature/MIME/extension checks, and private report-authorized downloads.
- Production evidence uploads deliberately return HTTP 503 until durable private storage and the required scanning, backup, retention, quota, and audit controls are configured. Do not enable public production uploads against Render's ephemeral filesystem.
- GitHub Actions on the production-upload safety commit `9c6a792220bac3fb5e70286c9e5c17d50f0ab4b7`: backend tests passed; frontend build passed.
- Phase 1 geographic foundation is complete: citizens can select a home State/LGA and independently report an incident in any State/LGA. The API validates State/LGA parent-child relationships.
- **Phase 2 scope:** administrator-managed geographic scopes for staff; server-side geographic authorization across report lists/details, assignments, status updates, attachments, history, and comments; automatic LGA/state-to-department routing with an unassigned triage queue; and a national admin drill-down from geopolitical zone to State to LGA.
- **Security rule:** frontend filters are not authorization. Staff must not access reports or evidence outside their assigned geographic scope. Citizens' home locations remain private and must never determine incident routing.
- **Not yet implemented in this branch:** staff geographic scopes, geographic authorization, automatic department routing, map-pin/boundary verification, and the national geographic admin drill-down.
- **Evidence storage remains a launch blocker:** choose and configure private durable object storage, malware scanning/quarantine, backup/restore, quotas, retention/deletion, and access auditing before enabling uploads in production.
- Local Windows/browser validation has not been performed from the user's workstation.

Resume commands (Windows PowerShell):
```powershell
cd C:\Users\gentle\govconnectx
git fetch origin
git switch feature/geographical-zones-phase-2
git pull --ff-only origin feature/geographical-zones-phase-2
```

Next: implement the Phase 2 backend scope model and administrator controls first, then enforce scopes in every staff report/evidence endpoint, add automatic routing and regression tests, and build the admin geographic drill-down. Run backend tests and frontend type-check/build before opening a PR. Never merge until CI passes.



## Current development checkpoint — Geographical Zones Phase 2

**Date:** 9 November 2026  
**Branch:** \`feature/geographical-zones-phase-2\`  
**Pull request:** [#19 — WIP: Phase 2 geographic department scopes and access control](https://github.com/cikwom/govconnectx/pull/19) (draft; do not merge yet)

### Implemented on this branch

- Added \`department_geographic_scopes\`: each department can cover a whole State or selected LGAs.
- Added system-admin endpoints:
  - \`GET /api/v1/departments/{department_id}/geographic-scopes\`
  - \`PUT /api/v1/departments/{department_id}/geographic-scopes\`
  - \`GET /api/v1/departments/{department_id}/routing-categories\`
  - \`PUT /api/v1/departments/{department_id}/routing-categories\`
- State/LGA combinations are validated; an LGA from a different State is rejected.
- Staff report lists and report details are filtered by department jurisdiction. The shared report authorization check also protects status changes, history, assignment records, comments, and evidence upload/list/download.
- Department assignment is rejected when the department has no matching geographic scope.
- Added category-based routing configuration. A report is automatically assigned only when exactly one active department matches both its category and incident State/LGA.
- Reports with no matching department, or with multiple matching departments, remain unassigned for national admin triage.
- Added \`GET /api/v1/admin/reports/unassigned\`.
- Added \`GET /api/v1/admin/geography/overview\`, returning report totals from geopolitical zone → State → LGA.
- \`ReportResponse\` now includes \`department_id\` so a citizen can see which department received the report.
- Backend regression tests cover geographic access restrictions, invalid State/LGA pairs, auto-routing, ambiguous routing, unassigned triage, and national geographic drill-down.

### Important behavior

- Routing uses the incident State/LGA, never the citizen's home State/LGA.
- A department with no configured scope cannot access geographically scoped reports.
- Automatic routing is deliberately conservative: exactly one eligible department is required. No match or multiple matches must be handled in the national triage queue.
- Production evidence uploads remain disabled until durable private object storage and the required security controls are implemented.

### CI and testing status

- Frontend build checks have passed on earlier PR revisions.
- An earlier backend run exposed a missing geographic fixture in the official-access test and missing \`department_id\` in the report response. Both were corrected.
- Latest backend and frontend checks are running against the latest branch revision. Record the final result in \`docs/testing/TEST_EVIDENCE.md\`; do not treat an in-progress run as a pass.
- Browser/manual validation on the Windows development machine has not yet been completed.

### Still pending before merge

1. Confirm latest backend CI passes; fix any remaining failures.
2. Build the Admin UI for managing department geographic scopes and routing categories.
3. Connect the national geographic drill-down and unassigned triage queue to the Admin UI.
4. Add incident GPS-vs-selected-State/LGA mismatch review. Do not silently overwrite a citizen-selected location from GPS.
5. Complete manual browser/API regression and update \`docs/testing/TEST_EVIDENCE.md\`.
6. Review the PR diff and CI, then merge only after all required checks pass.

### Resume commands (Windows PowerShell)

\\\`\\\`\\\`powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch feature/geographical-zones-phase-2
git pull --ff-only origin feature/geographical-zones-phase-2
\\\`\\\`\\\`
