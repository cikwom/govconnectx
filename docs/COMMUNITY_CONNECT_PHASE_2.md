# Community Connect — Phase 2

**Branch:** `feature/community-connect-phase-2`

## Included in this phase

- Explicit community membership with join/leave controls and audit events.
- Posting, commenting and private evidence uploads require active membership.
- Read-only authenticated users can still view the text discussion feed without joining.
- Authenticated, membership-gated WebSocket events update discussion feeds immediately for posts, comments, evidence uploads, moderation and report conversion.
- The frontend falls back to 20-second polling if the live socket is unavailable.
- Private MP4, WebM and QuickTime video uploads (50 MiB maximum) use content-signature validation, private storage and the existing malware-scanning service.
- A post author can convert their discussion into one official report.
- Conversion derives State, LGA, Ward and Community from the selected verified community record, asks the citizen for a street/landmark description, and does not request GPS.
- Existing private photos and videos are carried into the official report evidence list.
- General report submission now accepts a street/landmark plus State and LGA without requiring map coordinates.

## Privacy and moderation

- Device GPS remains optional. Manual State/LGA/ward/community selection and a landmark description are supported.
- Community evidence downloads are authenticated and restricted to active members.
- Production uploads still require durable private object storage and a configured malware scanner.
- Only the original post author can convert that post into an official report; duplicate conversion is rejected.
- Existing official announcement and moderation role checks remain in force.

## API additions

- `GET /api/v1/community-spaces/{community_code}/membership`
- `POST /api/v1/community-spaces/{community_code}/membership`
- `DELETE /api/v1/community-spaces/{community_code}/membership`
- `POST /api/v1/community-spaces/posts/{post_id}/attachments`
- `GET /api/v1/community-spaces/posts/{post_id}/attachments`
- `GET /api/v1/community-spaces/posts/{post_id}/attachments/{attachment_id}`
- `POST /api/v1/community-spaces/posts/{post_id}/convert-to-report`

## Remaining work

- Live WebSocket broadcasts currently use an in-process connection manager; horizontal multi-worker deployments will need shared pub/sub (for example Redis) so events reach sockets connected to other workers.
- Add moderation queues, post/member reporting, spam controls, and community admin roles.
- Validate video playback and upload performance with production storage.
- Run end-to-end tests for join/leave, evidence visibility, conversion, and the complete landmark-only citizen report flow.
- Verify the phase-two Alembic migration against a production-like PostgreSQL database before deployment.
