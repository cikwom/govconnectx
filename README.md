# GovConnect Nigeria

GovConnect Nigeria is an early-stage citizen-reporting backend API built with **Python**, **FastAPI**, **SQLAlchemy**, **Pydantic**, and **SQLite**.

## Current implementation

- FastAPI application: `backend/app/main.py`
- Database configuration: `backend/app/database.py`
- Citizen report model and API: `backend/app/models/report.py`, `backend/app/routers/reports.py`
- User model and authentication: `backend/app/models/user.py`, `backend/app/routers/auth.py`
- Password hashing, JWT handling, and role dependencies: `backend/app/core/`
- Request/response schemas: `backend/app/schemas/`

## Authentication and roles

The authentication API is mounted at `/api/v1/auth`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Public | Register a citizen account |
| POST | `/api/v1/auth/login` | Public | Verify credentials and issue a JWT access token |
| GET | `/api/v1/auth/me` | Authenticated | Return the current user's profile |
| PATCH | `/api/v1/auth/users/{user_id}/role` | System administrator | Assign an account role |

Supported roles:

- `citizen`
- `official`
- `department_admin`
- `supervisor`
- `system_admin`

Public registration always creates a `citizen`. Government and administrator roles must be assigned by a system administrator. The first system administrator is created through the local bootstrap command below.

Passwords are hashed using PBKDF2-HMAC-SHA256 with a random salt and 600,000 iterations. Login returns a signed JWT access token; protected routes expect it in the `Authorization: Bearer <token>` header. Tokens expire after 30 minutes by default.

### Report access rules

All report endpoints now require authentication.

- Citizens can create reports and list/read only reports they submitted.
- Officials, department administrators, supervisors, and system administrators can list/read reports across the platform.
- Reports created by authenticated users are linked to their account.
- Existing reports from the earlier database schema retain a null owner and are not visible to citizen accounts.

## Report API

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/` | Public | API-running response |
| POST | `/api/v1/reports` | Authenticated | Create a report |
| GET | `/api/v1/reports` | Authenticated | List reports according to role |
| GET | `/api/v1/reports/{report_id}` | Authenticated | Retrieve an authorized report |

## Local setup

Use Python 3.12 or a compatible Python version.

### Linux / macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload
```

The SQLite URL is relative to the current working directory, so run Uvicorn from `backend/`. Set a strong, random `JWT_SECRET` in `backend/.env` or the deployment environment. Production mode refuses to use the development fallback secret.

Interactive API documentation: http://127.0.0.1:8000/docs

## Create the first system administrator

From the `backend/` directory with the virtual environment active:

```bash
python -m scripts.create_system_admin
```

The command prompts for the administrator email, name, and password. It refuses to create another system administrator if one already exists. Keep this command and the administrator credentials private.

## Run tests

From the `backend/` directory:

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow currently runs **14 passing tests** covering password hashing, JWT handling, registration/login, current-user profiles, citizen report isolation, official report visibility, role assignment permissions, and migration of an existing reports table.

## Security and production gaps

This is an initial authentication/RBAC implementation, not a complete production security review. Before public deployment, add and verify:

- Login and registration rate limiting, email verification, and account recovery.
- Refresh-token rotation or a documented re-authentication strategy; access tokens are currently stateless and expire after 30 minutes.
- Audit logs for privileged role changes and administrative actions.
- More granular department/organization scoping for officials; staff roles currently have platform-wide report read access.
- Production database, HTTPS, secret management, backups, monitoring, and deployment hardening.
- A managed migration system such as Alembic as the schema grows; the current startup migration only adds the report owner column and index to legacy databases.

## Project checkpoint

See [GOVCONNECT_PROGRESS.md](GOVCONNECT_PROGRESS.md) for the implementation history and current development checkpoint.
