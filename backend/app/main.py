from fastapi import FastAPI
from app.database import Base, engine, migrate_existing_schema
from app.models import Department, Report, ReportAssignment, ReportComment, ReportStatusHistory, User  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.departments import router as departments_router
from app.routers.reports import router as reports_router

Base.metadata.create_all(bind=engine)
migrate_existing_schema()

app = FastAPI(title="GovConnect Nigeria", version="1.2.0")

@app.get("/")
def root():
    return {"message": "GovConnect Nigeria API is running"}

app.include_router(auth_router)
app.include_router(departments_router)
app.include_router(reports_router)
