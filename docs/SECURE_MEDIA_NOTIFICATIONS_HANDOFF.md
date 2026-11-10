# Secure Media and Notifications — Handoff

**Repository:** `cikwom/govconnectx`  
**Branch:** `feature/secure-media-and-notifications`  
**Base:** `main` after PR #22 merge.

## Implemented

- Added S3-compatible private object storage support for report evidence.
- Persisted per-attachment storage backend so local and object-store files are routed correctly on download.
- Added database migration for the new `storage_backend` column on existing attachment tables.
- Added ClamAV INSTREAM malware scanning; production/Render evidence uploads fail closed unless private object storage credentials and scanner host are configured and scanner returns a clean result.
- Kept object downloads behind the existing authenticated report authorization check; no public object URLs are issued.
- Added upload audit events.
- Added SMTP notification delivery using FastAPI background tasks for automatic routing, assignments, status changes and escalation requests.
- Email delivery respects the saved email notification preference. SMTP is a safe no-op when not configured.
- In-app notification listing/unread count respects the user's in-app notification preference.
- Documented Render environment variables, private bucket requirements and Neon/object-storage backup/restore requirements in `docs/PRODUCTION_STORAGE_NOTIFICATIONS_BACKUPS.md`.
- Extended root `.env.example` with storage, ClamAV and SMTP variables.

## Required production configuration

Set these in Render only, never in Git:
- `OBJECT_STORAGE_BUCKET`
- `OBJECT_STORAGE_ACCESS_KEY_ID`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY`
- `OBJECT_STORAGE_REGION`
- `OBJECT_STORAGE_ENDPOINT_URL` where required
- `CLAMAV_HOST` and optional port/timeout
- SMTP variables if email delivery is required

The object bucket must be private and encrypted at rest. Configure least-privilege credentials, object versioning/backup, and retention. The malware scanner must be reachable from the backend service.

## Validation status

- No local backend test suite or frontend typecheck/build has been run in this session.
- S3-compatible storage and ClamAV integration have not been exercised against real provider services.
- SMTP delivery has not been exercised against a real mail provider.
- Check GitHub Actions after PR creation and run local tests before treating this as production-ready.
- Do not enable production evidence uploads until Render environment variables, private bucket policy, ClamAV connectivity, backup/restore, and authenticated upload/download have been verified.

## Next work

1. Run tests and frontend build; fix any failures.
2. Add provider integration tests/mocks for S3, ClamAV and SMTP.
3. Add delivery retries, dead-letter visibility and provider webhooks.
4. Add retention/deletion and orphaned-object cleanup.
5. Add SMS/push only after verified phone ownership and consent.
6. Complete privacy, security, accessibility and load testing.
