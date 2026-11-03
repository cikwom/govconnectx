# GovConnect Nigeria — Development Checkpoint

**Repository:** https://github.com/cikwom/govconnectx  
**Base branch:** `main`  
**Working branch:** `feature/report-evidence-attachments-phase-4`  
**Checkpoint date:** 3 November 2026

## Current Git status

- Phase 1 authentication/RBAC is merged into `main`.
- Phase 2 department-based report management is merged into `main` by PR #2.
- Phase 3 in-app notifications and SLA tracking is merged into `main` by PR #3.
- Phase 3 merge commit: `0b750383cded4c517fe48e44a95dd565480473bf`.
- Phase 3 latest-head CI passed on commit `555466a01804b2856ef59c2e4aedf3a4d3b60c99`; PR #3 was marked ready and squash-merged.
- Phase 4 working branch: `feature/report-evidence-attachments-phase-4`.
- Phase 4 implementation commit: `eea5b888fb7bcfcfdb5a9e54041a97e3e66fc416`.
- Phase 4 has not yet been merged. Keep `main` unchanged and use a pull request.
- GitHub reports the `main` branch as unprotected. Enable branch protection in repository settings when admin access is available; do not assume it is active.

## Phase 1 — authentication and RBAC — merged

- Citizen registration and login with PBKDF2 password hashes and JWT access tokens.
- Roles: citizen, official, department_admin, supervisor, system_admin.
- Authenticated report creation and citizen ownership filtering.
- System-admin role management and first-admin bootstrap script.
- GitHub Actions backend test workflow.

## Phase 2 — report management workflow — merged

- Department creation and staff department assignment.
- Report assignment to departments and active staff members.
- Assignment records preserve who assigned a report, to whom, when, and any note.
- Validated status transitions and status history.
- Public comments and staff-only internal notes.
- Role/department-based report access scopes.
- Compatibility migration for department and assignment fields.

## Phase 3 — notifications and SLA tracking — merged

- Authenticated in-app notification inbox, unread count, and read actions.
- Report assignment and status changes notify relevant report owners/assignees.
- Configurable SLA deadline via `REPORT_SLA_HOURS` (default 72 hours).
- Resolution timestamp; reopening resets the SLA deadline.
- `GET /api/v1/sla/summary` provides role-scoped active, overdue, due-within-24-hours, and missing-deadline counts.
- Notifications are in-app only; no email/SMS provider is connected.

## Phase 4 — report evidence attachments — in progress

Implemented on `feature/report-evidence-attachments-phase-4`:

- New `ReportAttachment` metadata model with report, uploader, original filename, storage key, content type, byte size, SHA-256 digest, and timestamp.
- Authenticated upload endpoint: `POST /api/v1/reports/{report_id}/attachments`.
- Authenticated metadata listing endpoint: `GET /api/v1/reports/{report_id}/attachments`.
- Authenticated download endpoint: `GET /api/v1/reports/{report_id}/attachments/{attachment_id}/download`.
- Access is checked using the existing report authorization rules: citizens can access their own report evidence; staff access follows existing department/assignment scopes.
- Accepted formats are JPEG, PNG, and PDF. Content signatures and filename extensions are checked; unsupported or mismatched files are rejected.
- Default upload limit is 10 MiB; configure with `REPORT_ATTACHMENT_MAX_BYTES`.
- Files are stored under `REPORT_ATTACHMENT_DIR`, defaulting to `./private_uploads/report-evidence`, using random UUID storage names. Do not place this directory under a public static/web root.
- Downloads are sent as attachments with `application/octet-stream`, `nosniff`, and private/no-store caching.
- `python-multipart` added for multipart upload handling.
- Added attachment API tests for upload/list/download, cross-citizen access denial, and invalid/mismatched content.
- Backend API only at this stage; no frontend upload UI or cloud object-storage integration has been added.

## Phase 4 verification still required

1. Run the full backend test suite in GitHub Actions against the Phase 4 branch head; fix any failures before merging.
2. Add a test for the configured upload-size limit and a test for an authorized department official accessing evidence.
3. Confirm the production storage location is durable, private, backed up, and outside the web root. Local filesystem storage is the current implementation; object storage is a future production hardening option.
4. Add deployment environment settings for `REPORT_ATTACHMENT_DIR` and, if needed, `REPORT_ATTACHMENT_MAX_BYTES`.
5. Confirm existing production database startup creates the new attachment metadata table without data loss.
6. Back up the existing SQLite database before any production migration/startup test.
7. Enable and verify `main` branch protection in GitHub settings; the connected GitHub integration cannot configure or confirm it.

## Production hardening backlog

- Confirm production database, strong JWT secret, HTTPS, backups, rate limiting, monitoring, and durable private file storage.
- Consider Alembic migrations as schema complexity grows.
- Consider malware scanning and content-disarm/reconstruction for user-uploaded files before production use.
- Build citizen and official frontend upload/evidence views.
- Consider cloud object storage with private buckets and short-lived signed downloads.

## Resume commands

```bash
git fetch origin
git switch feature/report-evidence-attachments-phase-4
git pull --ff-only origin feature/report-evidence-attachments-phase-4
cd backend
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m uvicorn app.main:app --reload
```

Before merging Phase 4, confirm all checks are green on the latest branch head and the PR is mergeable.
