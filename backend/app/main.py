import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, migrate_existing_schema
from app.models import Department, Report, ReportAssignment, ReportAttachment, ReportComment, ReportStatusHistory, User
from app.models.notification import Notification  # noqa: F401
from app.routers.admin import router as admin_router
from app.routers.attachments import router as attachments_router
from app.routers.auth import router as auth_router
from app.routers.departments import router as departments_router
from app.routers.notifications import router as notifications_router
from app.routers.reports import router as reports_router
from app.routers.sla import router as sla_router

Base.metadata.create_all(bind=engine)
migrate_existing_schema()

app = FastAPI(title="GovConnect Nigeria", version="1.5.0")
cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

@app.get("/")
def root():
    return {"message": "GovConnect Nigeria API is running"}

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(departments_router)
app.include_router(reports_router)
app.include_router(attachments_router)
app.include_router(notifications_router)
app.include_router(sla_router)
