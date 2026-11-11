import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, migrate_existing_schema, SessionLocal
from app.models import Community, Department, LocalGovernmentArea, Report, ReportAssignment, ReportAttachment, ReportComment, ReportStatusHistory, State, User, Ward
from app.models.audit_event import AuditEvent  # noqa: F401 - register audit table before create_all
from app.models.citizen_services import CommunityListing, PublicServiceDirectoryEntry, ReportEscalation, ReportFeedback  # noqa: F401
from app.models.notification import Notification  # noqa: F401\nfrom app.models.password_reset_token import PasswordResetToken  # noqa: F401\nfrom app.models.auth_security_event import AuthSecurityEvent  # noqa: F401
from app.models.notification_delivery import NotificationDelivery  # noqa: F401
from app.models.phone_verification import PhoneVerification  # noqa: F401
from app.models.user_preference import UserPreference  # noqa: F401
from app.routers.admin import router as admin_router
from app.routers.attachments import router as attachments_router
from app.routers.auth import router as auth_router
from app.routers.departments import router as departments_router
from app.routers.citizen_services import router as citizen_services_router
from app.routers.locations import router as locations_router, seed_location_directory
from app.routers.notifications import router as notifications_router
from app.routers.public import router as public_router
from app.routers.preferences import router as preferences_router
from app.routers.reports import router as reports_router
from app.routers.sla import router as sla_router

Base.metadata.create_all(bind=engine)
migrate_existing_schema()
with SessionLocal() as location_session:
    seed_location_directory(location_session)

app = FastAPI(title="GovConnect Nigeria", version="1.7.0")
cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])


@app.get("/")
def root():
    return {"message": "GovConnect Nigeria API is running"}


app.include_router(auth_router)
app.include_router(locations_router)
app.include_router(admin_router)
app.include_router(departments_router)
app.include_router(citizen_services_router)
app.include_router(reports_router)
app.include_router(attachments_router)
app.include_router(notifications_router)
app.include_router(preferences_router)
app.include_router(sla_router)
app.include_router(public_router)
