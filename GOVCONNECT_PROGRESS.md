# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Working branch:** `feature/notifications-sla-phase-3`  
**Checkpoint date:** 3 November 2026

## Project status
GovConnect Nigeria is a FastAPI citizen-reporting API using SQLAlchemy, Pydantic, and SQLite. Phase 1 authentication and RBAC has been merged into `main`. Phase 2 report workflow is implemented on its own feature branch and must pass CI before merge.

## Phase 1 — merged
- Citizen registration and login with PBKDF2 password hashes and JWT access tokens.
- Roles: citizen, official, department_admin, supervisor, system_admin.
- Authenticated report creation and citizen ownership filtering.
- System-admin role management and first-admin bootstrap script.
- GitHub Actions backend test workflow.

## Phase 2 — report management workflow
Implemented on `feature/report-management-phase-2`:
- Departments can be created by system administrators and listed by authenticated users.
- Staff users can be assigned to departments by system administrators.
- Reports can be assigned to a department and optionally an active staff member in that department.
- Assignment records preserve who assigned a report, to whom, when, and any note.
- Report status transitions are validated: SUBMITTED → UNDER_REVIEW / REJECTED; UNDER_REVIEW → ASSIGNED / REJECTED; ASSIGNED → IN_PROGRESS / UNDER_REVIEW / REJECTED; IN_PROGRESS → RESOLVED / UNDER_REVIEW / REJECTED; terminal RESOLVED/REJECTED reports may be reopened to UNDER_REVIEW.
- Status history records actor, previous/new status, timestamp, message, and visibility.
- Comments support internal staff-only notes and citizen-visible comments.
- Citizens see only their own reports and public history/comments.
- Officials see only reports assigned to them within their department; department admins and supervisors see reports in their department; system admins retain platform-wide access.
- Existing databases receive nullable department/assignee columns and department indexes through the compatibility migration. New workflow tables are created by SQLAlchemy metadata.

## API routes added
- POST /api/v1/departments — system admin creates a department.
- GET /api/v1/departments — authenticated department listing.
- PATCH /api/v1/departments/members/{user_id} — system admin assigns/removes a staff member's department.
- POST /api/v1/reports/{report_id}/assignments — authorized department manager/supervisor or system admin assigns a report.
- GET /api/v1/reports/{report_id}/assignments — staff assignment history.
- PATCH /api/v1/reports/{report_id}/status — staff updates status through allowed transitions.
- GET /api/v1/reports/{report_id}/history — report status history; citizens see public entries only.
- POST/GET /api/v1/reports/{report_id}/comments — comments; internal notes hidden from citizens.

## Tests
New workflow tests cover department creation/listing, report assignment, department isolation, status transitions/history, and internal comment privacy. Full suite must pass in GitHub Actions before merging.

## Remaining review items
1. Confirm the local existing SQLite database backup and migration preserve all records.
2. Decide whether department admins should be allowed to assign staff to their own department (currently only system admins can set staff department membership).
3. Add pagination, file attachments/evidence, notifications, SLA/overdue tracking, and audit events as later phases.
4. Consider replacing startup compatibility migration with Alembic before schema complexity increases.
5. Production deployment still needs strong JWT secret, production database, HTTPS, backups, rate limiting, and monitoring.

## Resume and verify
```bash
git fetch origin
git switch feature/report-management-phase-2
git pull --ff-only origin feature/report-management-phase-2
cd backend
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m uvicorn app.main:app --reload
```

Do not merge into `main` until GitHub Actions passes and local database migration is verified.


## Phase 2 corrective review — pushed
- Restricted department managers from taking reports already routed to another department.
- Improved workflow test cleanup and migration regression coverage for idempotency and preservation of existing report rows.
- Phase 2 PR #2 remains open and unmerged; its latest changes require a fresh CI run.

## Phase 3 — notifications and SLA tracking
- In-app notifications are created for report assignment and status changes.
- Added authenticated notification inbox, unread count, mark-one-read, and mark-all-read endpoints.
- Added configurable report SLA deadline (REPORT_SLA_HOURS, default 72 hours) and resolution timestamp.
- Added SLA summary endpoint for active, overdue, due-within-24-hours, and missing-deadline reports, scoped to the caller.
- Added compatibility migration for SLA columns and index.
- Email/SMS delivery is not included; this phase uses in-app notifications without an external provider.

### Verification still required
- Phase 2 corrective CI passed on commit 690ca4b (run 41644318542).
- Phase 3 CI passed on commit d2fde44 (run 41645048150); notification/SLA endpoint regression coverage is being added next.
- Verify migration against a backed-up local SQLite database before production rollout.
- Set REPORT_SLA_HOURS to the actual service target.
- Enable main branch protection in GitHub settings; the connected GitHub integration lacks administration permission to configure or verify it.
