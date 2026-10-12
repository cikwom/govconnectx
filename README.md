# GovConnect Nigeria

GovConnect Nigeria is a backend API project built with **Python**,
**FastAPI**, **SQLAlchemy**, and **SQLite**.

This README records the project's current setup and implementation so
development can continue from the current point without restarting or
repeatedly inspecting the same files.

## Current Project Status

-   Repository: `govconnectx`
-   Branch: `main`
-   Last observed Git status: clean and up to date with `origin/main`
-   Backend directory: `backend/`
-   API framework: FastAPI
-   Database: SQLite
-   ORM: SQLAlchemy
-   ASGI server: Uvicorn

## Project Structure

``` text
govconnectx/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   └── routers/
│   │       └── reports.py  # Imported by main.py; confirm the file exists
│   ├── govconnect.db
│   ├── requirements.txt
│   └── .venv/
└── README.md
```

The `routers/reports.py` path is referenced in `main.py`, but it was not
visible in the last shallow file listing. Confirm it exists if the
application fails to start.

## What Is Implemented So Far

### FastAPI application

The entry point is `backend/app/main.py`.

It currently: - Creates a FastAPI application titled **GovConnect
Nigeria**. - Sets the API version to `1.0.0`. - Defines a root endpoint
at `GET /`. - Includes the reports router from `app.routers.reports`. -
Calls SQLAlchemy's `Base.metadata.create_all(bind=engine)` to create
tables for models registered with the metadata.

The root endpoint returns:

``` json
{
  "message": "GovConnect Nigeria API is running"
}
```

### Database setup

The database configuration is in `backend/app/database.py`.

It currently: - Uses the SQLite URL `sqlite:///./govconnect.db`. -
Creates a SQLAlchemy engine with `check_same_thread=False`, which is
commonly used for SQLite in FastAPI applications. - Defines
`SessionLocal` for database sessions. - Defines `Base` for SQLAlchemy
models. - Provides `get_db()`, a generator dependency that yields a
database session and closes it afterward.

**Important:** The SQLite URL is relative to the process's current
working directory. Run the server from `backend/` so the database file
is created or accessed at `backend/govconnect.db`.

### Dependencies

The pinned dependencies are listed in `backend/requirements.txt`. They
include: - FastAPI `0.143.0` - SQLAlchemy `2.1.4` - Uvicorn `0.54.0`

## Running the Backend

From the repository root:

``` bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then open these local URLs in a browser: - API root:
http://127.0.0.1:8000/ - Interactive API documentation:
http://127.0.0.1:8000/docs

If startup fails, check the exact Python traceback first. One known
point to verify is whether `backend/app/routers/reports.py` exists and
correctly defines `router`.

## Current Known Limitations

This README documents only what was confirmed from the files inspected
so far. The report endpoints, database models, validation schemas, and
tests have not yet been confirmed, so they are not described as
completed features here.

## Development Approach

Continue from the existing code rather than rebuilding the project. Work
in small steps: 1. Confirm the current backend starts. 2. Verify the
reports router and its endpoints. 3. Inspect or implement the report
database model and schemas. 4. Test the API through `/docs`. 5. Add
tests and update this README as features are completed.