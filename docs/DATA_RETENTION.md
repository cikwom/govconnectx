# Data retention and cleanup

## Implemented cleanup

The notification worker runs a retention cleanup once per day.

- Phone verification challenge records are deleted after they are more than 24 hours old. They contain the phone number and keyed OTP digest; the OTP itself is never stored.
- Terminal notification delivery rows (`sent` or `failed`) can be deleted after an explicitly configured number of days.
- Queued and currently sending delivery rows are never removed by this cleanup.
- `NOTIFICATION_DELIVERY_RETENTION_DAYS=0` (the default) disables notification-delivery deletion. Set a positive value only after the organisation has approved a retention period.
- Cleanup is performed by the notification worker, so it will not run until the Render Background Worker is deployed.

## Not yet covered by automated retention

This batch does not delete user accounts, reports, report comments, evidence files, community listings, feedback, audit events or geographic reference data. Those records need separate retention, legal-hold, deletion and backup rules. Evidence-object deletion must be coordinated with database metadata and storage-provider lifecycle rules to avoid orphaned files or broken report history.

## Policy and privacy review required

Before public production, the platform owner and qualified Nigerian privacy counsel should approve:

- Retention periods for reports and attachments, including sensitive evidence.
- How deletion requests interact with legal holds, investigations, audit integrity and public accountability.
- Retention of consent/revocation evidence and notification delivery logs.
- Data-subject access, correction, export and erasure workflows.
- Backup retention and deletion propagation into backup expiry.
- The privacy information shown to users, including phone verification and SMS provider processing.

Do not set a short delivery retention period merely to reduce database size; ensure operational troubleshooting and any applicable legal requirements are considered. This document describes implemented technical cleanup, not a legal compliance certification.
