# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Working branch:** `feature/auth-rbac-phase-1`  
**Latest working commit:** `53d8f678211b7719f8a8a3a9aed2a012a07114b4`  
**Checkpoint date:** 3 November 2026

## Project status

GovConnect Nigeria is an early-stage citizen-reporting API built with FastAPI, SQLAlchemy, Pydantic, and SQLite.

Phase 1 authentication and role-based access control has been implemented on the feature branch. It has not been merged into `main`.

## Completed before this phase

- Basic FastAPI application and health/root endpoint.
- SQLAlchemy database/session setup.
- Report model, request/response schemas, and create/list/get endpoints.
- Repository hygiene: Python virtual environments, cache files, and local SQLite database excluded from the current Git tree.
- README updated to reflect the verified project structure.

## Phase 1: authentication and RBAC — implemented

### User accounts and credentials

- Added SQLAlchemy `User` model with unique email, full name, password hash, role, active flag, and creation timestamp.
- Public registration creates citizen accounts only.
- Email is normalized to lowercase and validated.
- Password minimum is 8 characters at API registration; hashes use PBKDF2-HMAC-SHA256, per-password random salt, and 600,000 iterations.
- Login verifies credentials and returns a signed JWT access token.
- JWT lifetime defaults to 30 minutes and can be configured with `ACCESS_TOKEN_MINUTES`.
- Added `GET /api/v1/auth/me` for the current authenticated profile.

### Roles and authorization

Supported roles:

- `citizen`
- `official`
- `department_admin`
- `supervisor`
- `system_admin`

- Added reusable current-user and role-check dependencies.
- Added system-admin-only role assignment endpoint.
- Added a local bootstrap script to create the first system administrator.
- Authorization checks the current role from the database, so role changes take effect without waiting for an existing JWT to expire.

### Report access protection

- All report routes now require a valid bearer token.
- New reports are linked to the submitting user.
- Citizens can only list and retrieve their own reports.
- Staff roles currently have platform-wide report read access.
- Unknown or inaccessible report IDs return 404.
- Added a nullable `user_id` relationship to reports.
- Added a startup compatibility migration to add `reports.user_id` and its index to older database schemas. Existing reports remain unowned and are hidden from citizen accounts.

### Configuration and tests

- Added `.env.example` and dotenv loading.
- Added configurable `DATABASE_URL`, `JWT_SECRET`, and `ACCESS_TOKEN_MINUTES`.
- Production mode refuses to start without a configured JWT secret of at least 32 characters.
- Added PyJWT, python-dotenv, and HTTPX dependencies.
- Added unit and API tests.
- Added GitHub Actions workflow to install dependencies and run the backend test suite.

## Verification

<badge>14 tests passed</badge>

Latest GitHub Actions run: [Backend tests — successful](https://github.com/cikwom/govconnectx/actions/runs/41640402571)

The 14 passing tests cover:

- Password hashing, unique salts, wrong-password rejection, and malformed hashes.
- JWT claim creation and invalid-token rejection.
- Public registration always creating citizens.
- Login and current-user profile.
- Rejection of unauthenticated report access.
- Citizen report isolation.
- Official access to cross-citizen reports.
- Denial of role assignment to citizens.
- System administrator role assignment.
- Migration of a legacy reports table to include owner column and index.

## Files added or updated

- `.env.example`
- `.github/workflows/backend-tests.yml`
- `backend/app/config.py`
- `backend/app/core/security.py`
- `backend/app/core/dependencies.py`
- `backend/app/models/user.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/auth.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/reports.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/scripts/create_system_admin.py`
- `backend/tests/test_security.py`
- `backend/tests/test_auth_api.py`
- `backend/tests/test_database_migration.py`
- `backend/requirements.txt`
- `README.md`

## Remaining checks before merging into main

1. Run the app locally against the user's existing database after making a backup. Confirm the startup migration adds the owner column and preserves existing report rows.
2. Confirm `backend/.env` contains a strong `JWT_SECRET` before deploying. Never use the development fallback secret in production.
3. Run the first-system-admin bootstrap command locally and verify login.
4. Review whether staff should see all reports or only reports assigned to their department. Department and organization scoping are not implemented yet.
5. Add login/registration rate limiting, account recovery/email verification, and administrative audit logs before public launch.

The automated test suite passed in GitHub Actions. The local existing database and production deployment environment have not been exercised in this session.

## Git workflow

- The feature branch is on GitHub for review and automated testing.
- `main` has not been changed by this authentication implementation.
- Merge this phase only after the local database and administrator-bootstrap checks above are confirmed.

## Resume commands

From a local clone:

```bash
git fetch origin
git switch feature/auth-rbac-phase-1
git pull --ff-only origin feature/auth-rbac-phase-1
git status
cd backend
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m uvicorn app.main:app --reload
```
