# Production evidence storage, notifications and backups

## Evidence storage architecture

GovConnectX now supports an S3-compatible private object storage backend for report evidence.

- Local development can continue using the private local filesystem.
- When S3 credentials and bucket configuration are present, new evidence is written to the S3-compatible bucket.
- The database records the storage backend for each attachment so old local attachments remain distinguishable from new object-storage attachments.
- S3 objects use generated opaque keys under `report-evidence/`; client filenames are metadata only.
- No public object URL is returned. Downloads are streamed through the authenticated API after existing report ownership/jurisdiction checks.
- SHA-256 is recorded as object metadata and in the attachment record.
- Provider-side bucket encryption should be enabled. An optional server-side-encryption header can be configured where supported.

## Production upload gate

When `ENVIRONMENT=production` or the deployment is detected as Render, uploads are rejected unless:
1. A bucket, access key and secret key are configured.
2. A ClamAV host is configured.
3. The scanner is reachable and returns a clean `INSTREAM` result for each file.

A missing/unavailable scanner fails closed. Infected or unscannable files are not stored. Local development may run without ClamAV, but production must not.

### Required Render environment variables

- `OBJECT_STORAGE_BUCKET`
- `OBJECT_STORAGE_ACCESS_KEY_ID`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY`
- `OBJECT_STORAGE_REGION` (use `auto` for providers such as R2 when required)
- `OBJECT_STORAGE_ENDPOINT_URL` (for S3-compatible providers; blank for AWS S3)
- `CLAMAV_HOST`
- Optional: `CLAMAV_PORT`, `CLAMAV_TIMEOUT_SECONDS`, `OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION`

Configure the bucket as private. Do not grant public read/list permissions. Restrict credentials to the required bucket and object operations. Store secrets only in Render environment settings, never in Git or frontend variables.

### Migration notes

Existing local evidence records retain `storage_backend=local`. New uploads use `storage_backend=s3` when S3 configuration is complete. Before moving an existing deployment to a new bucket, copy its existing evidence files and update a verified migration mapping; do not simply change the environment variable and strand old files.

## Email notifications

SMTP delivery is queued as a FastAPI background task for:
- Automatic department routing.
- Department assignment.
- Report status changes.
- Report escalation requests to system administrators.

Delivery checks the user's email notification preference. If SMTP is not configured, the notification remains in-app and email is skipped. SMTP failures are logged and do not roll back report workflow transactions.

Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, and TLS settings in Render. Use a verified sender/domain and a provider with delivery monitoring. SMS and push delivery are not included in this batch.

## Backup and recovery requirements

The code cannot create a reliable backup policy by itself. Configure and verify these operational controls before launch:

1. **Neon PostgreSQL:** enable the appropriate managed backup/PITR plan for the production project; record retention and restore-point objectives.
2. **Object storage:** enable bucket versioning or an equivalent recovery control, encryption at rest, lifecycle/retention rules, and a separate backup copy for evidence that must be retained.
3. **Database/object consistency:** attachment rows and objects must be restored to compatible points in time. Retain object versions long enough to cover the database recovery window.
4. **Restore drills:** regularly restore the database to a staging project and verify representative attachment downloads through the authenticated API.
5. **Access control:** separate production runtime credentials from backup credentials; use least privilege and rotate credentials.
6. **Monitoring:** alert on failed uploads, failed malware scans, SMTP delivery failures, database connection errors, and backup job failures.
7. **Incident response:** document who can disable uploads, rotate credentials, restore the database and recover object versions.

Do not claim that backups are active until the provider settings and a restore test have been verified.

## Remaining production security work

- Add durable email delivery retries/dead-letter monitoring and provider webhook handling.
- Add periodic malware rescanning and an explicit quarantine/review workflow.
- Add object lifecycle cleanup for orphaned files after failed database commits.
- Add formal data retention/deletion workflows and a privacy impact assessment.
- Review authentication token storage and implement hardened refresh/session handling.
- Run dependency, API authorization, penetration, load and accessibility testing before public launch.
