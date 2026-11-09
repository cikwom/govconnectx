# Report photos, videos, and geographic evidence

## User reporting experience

A citizen selects the incident State and LGA independently of their home area, describes the issue, and can attach supporting JPEG/PNG photos, PDF documents, or short MP4/WebM/MOV videos. The incident coordinates and State/LGA are recorded with the report so responders can locate it.

## Supported evidence types in this phase

- JPEG and PNG images: 10 MiB default limit.
- PDF documents: 10 MiB default limit.
- MP4, WebM, and QuickTime MOV videos: 50 MiB default limit.
- Limits can be changed with `REPORT_ATTACHMENT_MAX_BYTES` and `REPORT_VIDEO_MAX_BYTES`.
- Backend validates file signatures, declared MIME type, and filename extension.
- Evidence remains private behind authenticated report access checks; another citizen cannot list or download it.

## Critical production storage warning

The current implementation writes evidence to a local directory configured by `REPORT_ATTACHMENT_DIR`. Render's local filesystem is ephemeral unless a persistent disk is deliberately attached and correctly mounted. A persistent disk can be a temporary deployment choice, but it ties storage to a service/region and requires backups, access controls, capacity monitoring, and a retention policy.

For a multi-agency production service, prefer private object storage with:
- private buckets and no public object URLs;
- short-lived, server-authorised download URLs or authenticated proxy downloads;
- encryption in transit and at rest;
- malware scanning/quarantine before staff access;
- file-size/type limits and rate limiting;
- retention/deletion workflows and audit events;
- backups and tested restore procedures;
- clear regional hosting and cross-border transfer review under the Nigeria Data Protection Act.

Do not publish video evidence to a public bucket. Videos and photos may contain faces, vehicle plates, children, homes, or precise location data. Warn citizens not to put themselves at risk to capture evidence, allow reporting without media, and provide a way to report urgent danger without waiting for an upload.

## Geographic reporting principles

- Citizens can report incidents in any Nigerian State/LGA, not just their registered home area.
- The report's incident location determines its geographic queue.
- The State's geopolitical zone is derived from the canonical location directory for national summaries; citizens should not choose a zone manually.
- GPS coordinates should be captured from a map pin or device location with user confirmation; State/LGA and reverse-geocoded address are supporting labels, not a substitute for coordinates.
- When coordinates and selected State/LGA disagree, flag the report for triage rather than silently routing it to a potentially wrong agency.
- Staff must only access evidence after the backend confirms their department and geographic assignment.

## Still required before public launch

1. Replace ephemeral local evidence storage with private durable object storage.
2. Add image/video malware scanning and quarantine.
3. Add per-user upload quotas, throttling, and aggregate storage monitoring.
4. Add map pin selection and reverse-geocoding with a human correction path.
5. Implement staff geographic scopes and enforce them across report, attachment, history, comment, and assignment APIs.
6. Implement LGA triage and department routing, including a no-agency-configured exception queue.
7. Add an agency-facing map/list with evidence previews and audit logging.
8. Validate privacy notice, lawful basis, retention, and data processor/transfer terms with Nigerian privacy counsel.
