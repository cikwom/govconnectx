# GovConnect Nigeria

GovConnect Nigeria is an early-stage citizen-reporting backend API built with **Python**, **FastAPI**, **SQLAlchemy**, **Pydantic**, and **SQLite**.

This repository currently contains the API foundation and basic create/read operations for citizen reports. It is a development-stage project, not yet a production-ready government engagement platform.

## Current implementation

- FastAPI application: `backend/app/main.py`
- SQLite and SQLAlchemy session setup: `backend/app/database.py`
- Citizen report model: `backend/app/models/report.py`
- Report request/response schemas: `backend/app/schemas/report.py`
- Report endpoints: `backend/app/routers/reports.py`
- Pinned Python dependencies: `backend/requirements.txt`

### API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Basic API-running response |
| POST | `/api/v1/reports` | Create a report |
| GET | `/api/v1/reports` | List reports |
| GET | `/api/v1/reports/{report_id}` | Retrieve a report by ID |

Interactive API documentation is available at `/docs` when the development server is running.

### Report data

A report currently stores its title, description, category, latitude, longitude, optional address, status, and creation/update timestamps. New reports default to the `SUBMITTED` status.

## Project structure

```text
govconnectx/
├── .gitignore
├── GOVCONNECT_PROGRESS.md
├── README.md
└── backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── database.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── report.py
    │   ├── routers/
    │   │   └── reports.py
    │   └── schemas/
    │       ├── __init__.py
    │       └── report.py
    └── requirements.txt
```

Local virtual environments, Python cache files, environment files, and SQLite database files are excluded from Git by `.gitignore`. The database is created locally when the application runs; it is not committed to the repository.

## Run the backend locally

Use Python 3.12 or a compatible Python version supported by the pinned dependencies.

### Linux / macOS

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Windows PowerShell

From the repository root:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The SQLite connection string is relative to the current working directory, so start Uvicorn from `backend/`.

Once the server starts, open:

- API root: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs

## Known gaps to address

The following items were not found in the code inspected so far and need a full implementation audit before development proceeds:

- Authentication and secure user accounts.
- Role-based authorization for citizens, officials, departments, and administrators.
- Report assignment and a complete report status workflow.
- Official responses, citizen progress tracking, and audit history.
- Stronger request validation and explicit 404 handling for unknown report IDs.
- Automated tests, database migrations, rate limiting, and production monitoring.
- Production database configuration, such as PostgreSQL.

Do not assume these features are absent from every part of the repository until the complete codebase has been audited.

## Development checkpoint

See [GOVCONNECT_PROGRESS.md](GOVCONNECT_PROGRESS.md) for the detailed progress checkpoint, confirmed findings, known limitations, and recommended implementation stages.

**Next recommended task:** audit the complete backend and its runtime behavior, then design authentication and role-based access control around the existing code rather than rebuilding the project.
