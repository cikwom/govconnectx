# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Working branch:** `feature/auth-rbac-phase-1`  
**Checkpoint date:** 3 November 2026

## Project status

GovConnect Nigeria is an early-stage citizen-reporting API built with FastAPI, SQLAlchemy, Pydantic, and SQLite.

## Completed before this phase

- Basic FastAPI application and health/root endpoint.
- SQLAlchemy database/session setup.
- Report model, request/response schemas, and create/list/get endpoints.
- Repository hygiene: Python virtual environments, cache files, and local SQLite database excluded from the current Git tree.
- README updated to reflect the verified project structure.

## Phase 1 implementation: authentication and RBAC

The current working branch contains the following implementation work:

### User accounts and credentials

- Added SQLAlchemy `User` model with unique email, full name, password hash, role, active flag, and creation timestamp.
- Public registration creates citizen accounts only.
- Email is normalized to lowercase.
- Password minimum is 8 characters at API registration; hashes use PBKDF2-HMAC-SHA256, per-password random salt, and 600,000 iterations.
- Added login that verifies credentials and returns a signed JWT access token.
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
- Role authorization checks the current role from the database, so role changes take effect without waiting for an existing JWT to expire.

### Report access protection

- All report routes now require a valid bearer token.
- New reports are linked to the submitting user.
- Citizens can only list and retrieve their own reports.
- Staff roles currently have platform-wide report read access.
- Unknown or inaccessible report IDs return 404.
- Added a nullable `user_id` relationship to reports.
- Added a small startup compatibility migration to add `reports.user_id` to an older database schema. Existing reports remain unowned and are hidden from citizen accounts.

### Configuration and tests

- Added `.env.example` and dotenv loading.
- Added configurable `DATABASE_URL`, `JWT_SECRET`, and `ACCESS_TOKEN_MINUTES`.
- Production mode refuses to start without a configured JWT secret of at least 32 characters.
- Added PyJWT and python-dotenv dependencies.
- Added unit tests for password hashing, password verification, and JWT handling.

## New/updated files

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
- `backend/requirements.txt`
- `.env.example`
- `README.md`

## Important remaining work before calling Phase 1 complete

1. Run the backend locally and verify startup against a clean SQLite database.
2. Verify startup against an existing database containing the original reports table; confirm the owner-column migration succeeds and old reports remain intact.
3. Install dependencies and run `python -m unittest discover -s tests -v`.
4. Test registration, login, current-user profile, and role assignment through Swagger.
5. Verify unauthenticated report requests return 401.
6. Verify a citizen cannot see another citizen's reports.
7. Verify a citizen receives 403 when attempting system-admin role assignment.
8. Verify the system administrator can assign the four elevated roles.
9. Add API integration tests and login rate limiting before production use.
10. Review department scoping: staff currently have platform-wide report visibility, not department-level filtering.

## Security limitations

- No refresh-token rotation or token revocation endpoint yet.
- No email verification, login rate limiting, or password-reset integration yet.
- No audit log for role changes.
- Staff role permissions are intentionally broad at this stage; department boundaries are not modeled.
- The migration is a small compatibility step, not a replacement for Alembic.
- The current tests are unit tests, not full API integration tests.

## Git workflow

- Keep this phase isolated on `feature/auth-rbac-phase-1`.
- Do not merge to `main` until the local verification checklist above has been completed.
- Once the phase is verified, push/merge it as one reviewed phase and then update this checkpoint.

## Resume commands

From a local clone:

```bash
git fetch origin
git switch feature/auth-rbac-phase-1
git status
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
