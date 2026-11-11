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
**Branch:** `feature/geographical-zones-phase-2`  
**Pull request:** [#19 — WIP: Phase 2 geographic department scopes and access control](https://github.com/cikwom/govconnectx/pull/19) (draft; do not merge yet)

### Implemented on this branch

- Added `department_geographic_scopes`: each department can cover a whole State or selected LGAs.
- Added system-admin endpoints:
  - `GET /api/v1/departments/{department_id}/geographic-scopes`
  - `PUT /api/v1/departments/{department_id}/geographic-scopes`
  - `GET /api/v1/departments/{department_id}/routing-categories`
  - `PUT /api/v1/departments/{department_id}/routing-categories`
- State/LGA combinations are validated; an LGA from a different State is rejected.
- Staff report lists and report details are filtered by department jurisdiction. The shared report authorization check also protects status changes, history, assignment records, comments, and evidence upload/list/download.
- Department assignment is rejected when the department has no matching geographic scope.
- Added category-based routing configuration. A report is automatically assigned only when exactly one active department matches both its category and incident State/LGA.
- Reports with no matching department, or with multiple matching departments, remain unassigned for national admin triage.
- Added `GET /api/v1/admin/reports/unassigned`.
- Added `GET /api/v1/admin/geography/overview`, returning report totals from geopolitical zone → State → LGA.
- `ReportResponse` now includes `department_id` so a citizen can see which department received the report.
- Added the Admin Geographic Operations panel for department scopes, routing categories, national triage and geographic drill-down. CORS permits the required authenticated PUT requests.
- Backend regression tests cover geographic access restrictions, invalid State/LGA pairs, auto-routing, ambiguous routing, unassigned triage, and national geographic drill-down.

### Important behavior

- Routing uses the incident State/LGA, never the citizen's home State/LGA.
- A department with no configured scope cannot access geographically scoped reports.
- Automatic routing is deliberately conservative: exactly one eligible department is required. No match or multiple matches must be handled in the national triage queue.
- Production evidence uploads remain disabled until durable private object storage and the required security controls are implemented.

### CI and testing status

- Backend tests passed on push run [42714191059](https://github.com/cikwom/govconnectx/actions/runs/42714191059) and frontend build passed on push run [42714191083](https://github.com/cikwom/govconnectx/actions/runs/42714191083), for code commit `bb41ece401d2e99be26ac94964f9ef12798c96dc`.
- Latest PR-triggered checks are still being confirmed. See `docs/testing/TEST_EVIDENCE.md`; do not treat an in-progress run as a pass.
- Browser/manual validation on the Windows development machine has not yet been completed.

### Still pending before merge

1. Confirm latest PR backend and frontend checks pass; fix any remaining failures.
2. Validate the Admin UI for department scopes, category routing, national drill-down and triage queue.
3. Add incident GPS-vs-selected-State/LGA mismatch review. Do not silently overwrite a citizen-selected location from GPS.
4. Complete manual browser/API regression and update `docs/testing/TEST_EVIDENCE.md`.
5. Review the PR diff and CI, then merge only after all required checks pass.

### Resume commands (Windows PowerShell)

```powershell
cd C:\Users\gentle\govconnectx
git fetch origin
git switch feature/geographical-zones-phase-2
git pull --ff-only origin feature/geographical-zones-phase-2
```


## Current development checkpoint — GPS incident-location review

**Date:** 10 November 2026  
**Branch:** `feature/geographical-zones-phase-2`  
**Pull request:** [#19](https://github.com/cikwom/govconnectx/pull/19) — open draft; not merged.

- Citizens can explicitly choose **Use my current location** during report submission. The browser asks for permission; declining or unsupported geolocation leaves manual coordinate entry available.
- Device GPS coordinates are stored separately from the incident coordinates and selected State/LGA. Capturing GPS may prefill the incident coordinate fields, but it never changes the selected State or LGA.
- Reports with shared GPS coordinates enter a `pending` human-review queue. Reports without GPS remain valid and are marked `not_provided`.
- System administrators can inspect GPS coordinates and the citizen-selected incident State/LGA, then record `verified`, `mismatch`, or `unable_to_verify` with an optional note. Reviewer ID and timestamp are retained.
- Review outcomes never silently rewrite the citizen's selected incident geography or alter the routing basis.
- Backend validation rejects incomplete GPS pairs and out-of-range/non-finite coordinates. Regression tests cover the GPS queue, admin-only review, selected-area preservation, and invalid GPS input.
- Latest code commit: `2e51b9f559f227575ddd8168b1d7658998c0e791` — GPS review tests. GitHub Actions for the latest changes were still running at checkpoint time; verify them before marking this work validated.
- **Manual checks still required:** test browser permission allow/deny on HTTPS, inspect the admin review queue, verify the three review outcomes, and confirm department routing remains based on selected incident State/LGA.
- This is an administrative human-review workflow, not automatic geospatial boundary validation. Do not describe GPS as proof that an incident occurred at the reported location.

Resume commands:
```powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch feature/geographical-zones-phase-2
git pull --ff-only origin feature/geographical-zones-phase-2
```


---

## Current development checkpoint — Accountability Engine expansion

**Date:** 10 November 2026  
**Repository:** `cikwom/govconnectx`  
**Current branch:** `main`  
**Latest merged feature PR:** [#28 — Ward-level department jurisdiction](https://github.com/cikwom/govconnectx/pull/28)  
**Latest merged commit:** `e575a61677ff02da471ee749273912e1978582f2`

The earlier geographic-zones and GPS checkpoint sections above describe historical work. The PR #19 status in the older checkpoint is superseded: the newer work has been merged through PRs #20–#26.

### Merged feature batches

- **PR #20:** Accountability audit events, protected audit log API, public aggregate transparency API/dashboard and roadmap.
- **PR #21:** Advisory duplicate hints, report escalation, post-resolution feedback, moderated Lost and Found, verified public service directory.
- **PR #22:** Department-scoped workload/SLA analytics, user preferences, starter English/Hausa/Yoruba/Igbo translations, keyboard skip navigation and reduced-motion support.
- **PR #23:** S3-compatible private evidence storage, ClamAV fail-closed scanning, SMTP background email notifications, notification preference enforcement and production storage/backup guidance.
- **PR #24:** Protected department staff directory, report assignment and status controls for authorized department staff and field officers.
- **PR #25:** GitHub Actions workflow for backend compile/tests and frontend production build.
- **PR #26:** Ward/community reference models and optional incident ward/community selection. Directory data must be entered from authoritative records; no codes or boundaries are fabricated.

### Production configuration still required

- Configure a private S3-compatible bucket and least-privilege credentials in Render.
- Configure a reachable ClamAV scanner before production evidence uploads; production/Render uploads fail closed until storage and scanner are ready.
- Configure SMTP variables and verify sender/domain before relying on email delivery.
- Configure Neon database backup/PITR and object storage versioning/backup, then perform a restore drill.
- Do not claim production backups or media storage are operational until provider settings and restore tests have been verified.

### Outstanding work

1. Add ward-level department jurisdiction rules and bulk import/validation for authoritative ward/community datasets.
2. Add SMS/push notification delivery only after phone verification and explicit consent.
3. Expand reviewed Hausa/Yoruba/Igbo translations across all screens and legal content.
4. Complete formal WCAG 2.2 AA, security, privacy, API authorization and load testing.
5. Add integration tests for S3, ClamAV, SMTP, escalation, feedback, moderation and role-based agency workflows.
6. Complete manual browser testing for citizen, official, department administrator, supervisor and system administrator accounts.
7. Implement retention/deletion, orphaned-object cleanup, delivery retries and monitoring.

### Validation status

The latest GitHub workflow was added in PR #25, but the GitHub integration did not return workflow-run results for the subsequent merged commits in this session. Do not assume the latest code has passed CI solely because PRs merged. Run the checks locally and verify Actions in GitHub.

### Resume commands — Windows PowerShell

```powershell
cd C:\Users\gentle\govconnectx
git fetch origin
git switch main
git pull --ff-only origin main

# Backend
cd backend
.\.venv\Scripts\python.exe -m compileall -q app
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Frontend (this repository currently has no committed package-lock.json)
cd ..\frontend
npm.cmd install
npm.cmd run build
```


---

## Current development checkpoint — Ward-level department jurisdiction

**Date:** 10 November 2026  
**Repository:** `cikwom/govconnectx`  
**Branch:** `main`  
**Merged PR:** [#28 — Ward-level department jurisdiction](https://github.com/cikwom/govconnectx/pull/28)  
**Merge commit:** `e575a61677ff02da471ee749273912e1978582f2`

### Completed

- Extended department geographic scopes from State/LGA to State/LGA/ward.
- Existing State/LGA scope records remain valid after migration; their new `ward_code` is null and does not silently narrow access.
- System Admin can select State → LGA → Ward in Geographic Operations.
- The API validates ward-to-LGA and LGA-to-State parent relationships and rejects inactive or incorrectly nested wards.
- Ward-aware authorization now covers staff report lists/details, manual department assignment, automatic category routing and department performance metrics.
- Ward-specific routing requires an exact incident ward match. State-wide and LGA-wide scopes continue to include reports with finer-grained ward data.
- Added regression coverage for ward visibility, invalid parent relationships, automatic routing and legacy database migration.
- Added `docs/WARD_LEVEL_JURISDICTION.md`.
- Fixed CI setup to use `npm install` because this repository does not currently commit `frontend/package-lock.json`.

### Validation

- Backend tests: **61 passed** in GitHub Actions.
- Frontend dependency audit, TypeScript type-check and production build: **passed** in GitHub Actions.
- CI runs on the merged PR head:
  - Backend: https://github.com/cikwom/govconnectx/actions/runs/42919811254
  - Frontend: https://github.com/cikwom/govconnectx/actions/runs/42919811303
  - Combined CI: https://github.com/cikwom/govconnectx/actions/runs/42919811257
- Manual browser validation on the Windows development machine is still outstanding.

### Remaining work

1. Build a controlled bulk import/validation process for authoritative ward/community records. Do not invent codes or boundaries; retain source attribution and effective dates.
2. Manually test two wards in one LGA with a department restricted to only one ward.
3. Add SMS/push delivery only after phone verification and explicit consent.
4. Complete full Hausa/Yoruba/Igbo translations, WCAG 2.2 AA review, security/privacy/load testing and integration tests for external services.
5. Configure and verify production S3-compatible storage, ClamAV, SMTP, database/media backups and restore drills before enabling production evidence uploads.

### Resume commands — Windows PowerShell

```powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch main
git pull --ff-only origin main

# Backend
cd backend
.\\.venv\\Scripts\\python.exe -m compileall -q app
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v

# Frontend (there is no committed package-lock.json yet)
cd ..\\frontend
npm.cmd install
npm.cmd run build
```


---

## Current development checkpoint — Authoritative geographic CSV imports

**Date:** 11 November 2026  
**Repository:** `cikwom/govconnectx`  
**Branch:** `main`  
**Merged feature PR:** [#30 — Authoritative ward and community CSV imports](https://github.com/cikwom/govconnectx/pull/30)  
**Merge commit:** `aa39a750b42d694446afd428599316fe13926fb2`

### Completed

- Added System Admin-only CSV preview and commit endpoints for ward and community reference records.
- CSV imports support up to 5,000 rows / 2 MB and validate record types, code/name limits, duplicate codes, existing-code conflicts, and LGA/ward parent relationships.
- Preview is read-only. Commit revalidates and rejects the entire batch if any row has an error.
- Existing records are never overwritten or deleted by bulk import.
- Each imported row records source name, source reference, effective date, import timestamp and importing administrator.
- Successful batches create an append-only audit event; public ward/community lookups expose source attribution and effective date.
- Added a System Admin UI with CSV template download, source details, validation preview, row-level errors and explicit commit.
- Added migration coverage and regression tests for authorization, preview-only behavior, successful import, provenance and all-or-nothing rejection.
- Documentation: `docs/GEOGRAPHIC_REFERENCE_IMPORT.md`.

### Validation

- Backend: **64 tests passed** in GitHub Actions.
- Frontend dependency audit, TypeScript check and production build: **passed**.
- Combined workflow: https://github.com/cikwom/govconnectx/actions/runs/43022253499
- PR #30: https://github.com/cikwom/govconnectx/pull/30

### Manual / production work still required

1. You must obtain and independently verify the actual ward/community data from INEC or the relevant State/LGA authority before importing it. No official dataset was fabricated or included.
2. Run the manual two-ward jurisdiction test in the Admin Command Centre.
3. Configure and verify production S3-compatible storage, ClamAV, SMTP, database/media backups and a restore drill.
4. Complete full Hausa/Yoruba/Igbo translations, WCAG 2.2 AA review, security/privacy/load testing and integration tests for external services.

### Next implementation batches

- Complete multilingual coverage across citizen, agency and administration experiences.
- Add consent-based SMS delivery and delivery status/retry monitoring.
- Continue accessibility and production-readiness hardening.

### Resume commands — Windows PowerShell

```powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch main
git pull --ff-only origin main

# Backend
cd backend
.\\.venv\\Scripts\\python.exe -m compileall -q app
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v

# Frontend
cd ..\\frontend
npm.cmd install
npm.cmd run build
```


---

## Current development checkpoint — Multilingual citizen experience

**Date:** 11 November 2026  
**Repository:** `cikwom/govconnectx`  
**Branch:** `main`  
**Latest merged feature PR:** [#32 — Hausa, Yorùbá and Igbo citizen experience](https://github.com/cikwom/govconnectx/pull/32)  
**Merge commit:** `11b0db9fdf5af0041b504d6343d07a4b7f88e7a6`

### Merged work since the previous checkpoint

- **PR #30:** System Admin-only CSV preview/commit for ward/community data; validates parent relationships, prevents overwrites, records source attribution and import audit events; adds a bulk-import interface and migration. Documentation: `docs/GEOGRAPHIC_REFERENCE_IMPORT.md`.
- **PR #31:** README checkpoint for the authoritative geography importer.
- **PR #32:** Expanded English/Hausa/Yorùbá/Igbo language selector and first-pass translations for public and citizen-facing screens; localized date formatting; translation-completeness check in GitHub Actions. Documentation: `docs/LOCALIZATION.md`.

### Validation evidence

- PR #30: 64 backend tests passed; frontend dependency audit, translation-independent typecheck/build passed.
- PR #32: 64 backend tests passed; translation completeness, frontend typecheck and production build passed.
- PR #32 Actions: https://github.com/cikwom/govconnectx/actions/runs/43024147242
- The translation check verifies key coverage and duplicate keys; it does not certify linguistic accuracy.

### Remaining implementation work

1. Complete Hausa/Yorùbá/Igbo localization for report details, agency/field-officer workflows, department performance, System Admin Command Centre and remaining operational components.
2. Add SMS delivery only with verified phone numbers and explicit user consent; add delivery status, retries and monitoring.
3. Complete accessibility review against WCAG 2.2 AA and security/privacy/load testing.
4. Complete manual browser testing for citizen, official, department administrator, supervisor and system administrator roles.
5. Configure and verify production private object storage, ClamAV, SMTP, managed database backups, media backups and restore drills.

### Manual tasks for the project owner

- Obtain and independently verify genuine ward/community reference data from INEC or the relevant State/LGA authority before importing. No codes or boundaries are fabricated.
- Manually test a department restricted to one of two wards in the same LGA.
- Before production, supply/verify provider credentials and sender/domain settings, and participate in a database/media restore drill.
- Arrange native-speaker review of Hausa, Yorùbá and Igbo interface translations and qualified Nigerian legal/privacy review before translating or publishing legal documents.

### Resume commands — Windows PowerShell

```powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch main
git pull --ff-only origin main

# Backend
cd backend
.\\.venv\\Scripts\\python.exe -m compileall -q app
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v

# Frontend
cd ..\\frontend
npm.cmd install
npm.cmd run check:translations
npm.cmd run typecheck
npm.cmd run build
```


---

## Current development checkpoint — Agency and report-detail localization

**Date:** 11 November 2026  
**Repository:** `cikwom/govconnectx`  
**Branch:** `main`  
**Latest merged feature PR:** [#34 — Report details and agency workflow localization](https://github.com/cikwom/govconnectx/pull/34)  
**Merge commit:** `09a7bf841a5649a8cf10f302547a742c8264629e`

### Completed since the previous checkpoint

- **PR #32:** Added English/Hausa/Yorùbá/Igbo language selection and first-pass translations for public and citizen-facing pages.
- **PR #33:** Updated the README checkpoint and resume steps.
- **PR #34:** Extended Hausa/Yorùbá/Igbo translations to report details, status history, comments, evidence upload/download, escalation, citizen feedback, agency officer workflows, department assignment, performance indicators and signed-in role labels.
- Localized report detail, citizen report and community-listing timestamps.
- Added translation completeness checks for literal UI keys plus dynamic workflow statuses, role names and landing-page feature strings.
- Documentation: `docs/LOCALIZATION.md`.

### Validation

- Backend: **64 tests passed**.
- Frontend: translation completeness, TypeScript typecheck and production build passed.
- PR #34 Actions: https://github.com/cikwom/govconnectx/actions/runs/43025101114

### Remaining localization work

1. Localize the full System Admin Command Centre, Geographic Operations, geographic directory/import, community moderation and audit log screens.
2. Review all first-pass translations with native Hausa, Yorùbá and Igbo speakers familiar with Nigerian public administration.
3. Keep Terms of Use and Privacy Notice in English until qualified Nigerian legal/privacy reviewers and competent translators approve the legal translations.

### Other remaining implementation and owner tasks

- Add consent-based SMS delivery with phone verification, delivery status, retry policy and monitoring.
- Complete WCAG 2.2 AA review, security/privacy/load testing and full browser tests for citizen, officer, department admin, supervisor and system admin roles.
- Independently obtain and verify official ward/community data from INEC or the relevant State/LGA authority before importing.
- Manually test a department restricted to one ward while another ward in the same LGA remains inaccessible.
- Before production, configure and verify private object storage, ClamAV, SMTP, database/media backups and restore drills.

### Resume commands — Windows PowerShell

```powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch main
git pull --ff-only origin main

# Backend
cd backend
.\\.venv\\Scripts\\python.exe -m compileall -q app
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v

# Frontend
cd ..\\frontend
npm.cmd install
npm.cmd run check:translations
npm.cmd run typecheck
npm.cmd run build
```


---

## Current development checkpoint — Accessibility foundations

**Date:** 11 November 2026  
**Repository:** `cikwom/govconnectx`  
**Branch:** `main`  
**Latest merged feature PR:** [#37 — Accessibility foundations](https://github.com/cikwom/govconnectx/pull/37)  
**Merge commit:** `45216a7a232a9614179b01d59a751e77de12b118`

### Completed

- **PR #30:** Authoritative ward/community CSV import with source attribution, parent validation, preview and explicit commit.
- **PR #32:** Hausa, Yorùbá and Igbo localization for public and citizen experiences.
- **PR #34:** Localization for report details and agency/field-officer workflows.
- **PR #36:** Localization for the System Admin Command Centre, geographic operations/import, moderation and audit screens.
- **PR #37:** Accessibility foundations: 44px interactive control heights, 24px checkbox/radio targets, dark-theme keyboard focus, increased-contrast and Windows forced-colors support.
- Added `frontend/scripts/check-accessibility.mjs` and wired it into GitHub Actions.
- Added `docs/ACCESSIBILITY_AUDIT.md` with the manual WCAG 2.2 AA verification plan.

### Validation for PR #37

- Translation coverage: **463 interface keys passed**.
- Accessibility foundation smoke checks: **8 passed**.
- Frontend dependency install, typecheck and production build: **passed**.
- Backend compile and unit tests: **passed**.
- CI run: https://github.com/cikwom/govconnectx/actions/runs/43037844247
- Frontend build run: https://github.com/cikwom/govconnectx/actions/runs/43037844249
- Backend test run: https://github.com/cikwom/govconnectx/actions/runs/43037844103

### Remaining work

1. Add SMS delivery only after verified phone numbers and explicit user consent; include delivery status, bounded retries and monitoring.
2. Complete the manual WCAG 2.2 AA audit with keyboard-only use, NVDA/VoiceOver, zoom/reflow, contrast and forced-colors testing. The automated checks are not proof of conformance.
3. Review Hausa, Yorùbá and Igbo interface translations with native speakers familiar with Nigerian public services. Keep legal documents in English until qualified legal/privacy and translation review is complete.
4. Complete security, privacy, API authorization, integration and load testing.
5. Complete manual role-based browser testing for citizens, officials, department administrators, supervisors and System Administrators.
6. Obtain and verify authoritative ward/community records before importing them.
7. Configure private production object storage, ClamAV, SMTP, managed database/media backups and perform a restore drill before production use.

### Manual owner tasks

- No immediate manual action is required to continue development.
- Before importing geographic data, obtain the genuine source files from INEC or the relevant State/LGA authority and verify their provenance.
- Before production, supply provider configuration and participate in the restore and role-based acceptance tests.

### Resume commands — Windows PowerShell

```powershell
cd C:\\Users\\gentle\\govconnectx
git fetch origin
git switch main
git pull --ff-only origin main

# Backend
cd backend
.\\.venv\\Scripts\\python.exe -m compileall -q app
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v

# Frontend
cd ..\\frontend
npm.cmd install
npm.cmd run check:translations
npm.cmd run check:accessibility
npm.cmd run typecheck
npm.cmd run build
```
