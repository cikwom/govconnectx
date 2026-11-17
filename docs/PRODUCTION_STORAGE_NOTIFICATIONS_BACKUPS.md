# Production evidence storage, notifications and backups

## Evidence storage architecture

GovConnectX supports an S3-compatible private object storage backend for report evidence.

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

### Required object-storage and scanner settings

- `OBJECT_STORAGE_BUCKET`
- `OBJECT_STORAGE_ACCESS_KEY_ID`
- `OBJECT_STORAGE_SECRET_ACCESS_KEY`
- `OBJECT_STORAGE_REGION` (use `auto` for providers such as R2 when required)
- `OBJECT_STORAGE_ENDPOINT_URL` (blank for AWS S3)
- `CLAMAV_HOST`
- Optional: `CLAMAV_PORT`, `CLAMAV_TIMEOUT_SECONDS`, `OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION`

Configure the bucket as private. Do not grant public read/list permissions. Restrict credentials to required bucket and object operations. Store secrets only in the backend service's secret environment, never in Git or frontend variables.

### Migration notes

Existing local evidence records retain `storage_backend=local`. New uploads use `storage_backend=s3` when S3 configuration is complete. Before moving an existing deployment to a new bucket, copy its existing evidence files and update a verified migration mapping; do not simply change the environment variable and strand old files.

## Email and SMS notification delivery

Report auto-routing, assignment, status changes and escalations create durable notification outbox rows for enabled channels.

- Email is queued when email notifications are enabled (or no preference record exists).
- SMS is queued only for an active account with a verified phone number, explicit SMS consent and no recorded consent revocation.
- SMS content is intentionally brief and does not include report titles or user-submitted content.
- The API attempts new deliveries; a separate worker processes scheduled retries and reclaims stale `sending` rows.
- Retry attempts are bounded (five total); failures are retained for admin monitoring rather than silently discarded.
- Admin monitoring masks destination addresses/numbers and does not expose message bodies.

Configure SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` and TLS settings) and Termii (`TERMII_API_KEY`, `TERMII_SENDER_ID`, optional `TERMII_API_URL` and `SMS_TIMEOUT_SECONDS`) in both the API and worker environments. Use verified sender identities and provider delivery monitoring.

Deploy the worker as a separate background process using `python -m app.workers.notification_worker`, the same `DATABASE_URL`, and the same delivery-provider secrets as the API. See [NOTIFICATION_OUTBOX.md](NOTIFICATION_OUTBOX.md) and [SMS_NOTIFICATIONS.md](SMS_NOTIFICATIONS.md).

**Delivery is at-least-once, not exactly-once.** A process crash after a provider accepts a message but before GovConnectX records success can cause a duplicate. Provider acceptance is not proof of handset/mailbox delivery. Provider receipt webhooks, permanent-failure classification and dead-letter review are not yet implemented. Do not rely on email/SMS for emergency dispatch.

## Backup and recovery requirements

The code cannot create or prove a reliable production backup policy by itself. Configure and verify these operational controls before launch:

1. **Managed PostgreSQL:** enable the appropriate managed backup/PITR plan for the production project; record retention and recovery-point/recovery-time objectives.
2. **Object storage:** enable bucket versioning or an equivalent recovery control, encryption at rest, lifecycle/retention rules, and a separate backup copy for evidence that must be retained.
3. **Database/object consistency:** attachment rows and objects must be restored to compatible points in time. Retain object versions long enough to cover the database recovery window.
4. **Restore drills:** regularly restore the database to a staging project and verify representative attachment downloads through the authenticated API.
5. **Access control:** separate production runtime credentials from backup credentials; use least privilege and rotate credentials.
6. **Monitoring:** alert on failed uploads, failed malware scans, notification delivery failures, database connection errors and backup job failures.
7. **Incident response:** document who can disable uploads, rotate credentials, restore the database and recover object versions.

Do not claim that backups are active until provider settings and a restore test have been verified.

## Remaining production security work

- Add provider delivery-receipt webhooks and permanent-failure classification.
- Add periodic malware rescanning, quarantine/review and orphaned-object cleanup.
- Complete formal data retention/deletion workflows and a privacy impact assessment.
- Review authentication token storage and hardened refresh/session handling.
- Run dependency, API authorization, penetration, load and accessibility testing before public launch.
