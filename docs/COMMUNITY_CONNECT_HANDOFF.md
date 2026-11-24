# Community Connect — Implementation Handoff

**Repository:** `cikwom/govconnectx`  
**Branch:** `feature/community-connect-foundation`  
**Pull request:** #79

## Included in this phase

- Authenticated community feeds selected through the existing State → LGA → Ward → Community directory.
- Text discussion posts and threaded comments.
- Official announcement publishing restricted to authorised government staff roles.
- Post hide/unhide moderation restricted to department administrators, supervisors, and system administrators.
- Audit events for post creation, comment creation, image uploads, and moderation actions.
- JPEG and PNG image attachments with file-signature, MIME type, extension, and size validation.
- Authenticated image listing and download endpoints with private/no-store response headers.
- Malware scanning through the existing ClamAV integration.
- Frontend Community Connect page with manual geography selection; it does not request device GPS.

## API

- `GET /api/v1/community-spaces/{community_code}/posts`
- `POST /api/v1/community-spaces/{community_code}/posts`
- `GET /api/v1/community-spaces/posts/{post_id}/comments`
- `POST /api/v1/community-spaces/posts/{post_id}/comments`
- `PATCH /api/v1/community-spaces/posts/{post_id}/moderation`
- `POST /api/v1/community-spaces/posts/{post_id}/images`
- `GET /api/v1/community-spaces/posts/{post_id}/images`
- `GET /api/v1/community-spaces/posts/{post_id}/images/{image_id}`

## Media safety and deployment

- Local development stores files under `COMMUNITY_MEDIA_DIR` (default: `./private_uploads/community-media`).
- `COMMUNITY_IMAGE_MAX_BYTES` controls the maximum image size (default: 10 MiB).
- Production uploads are refused unless private object storage and malware scanning are configured.
- Object storage uses the existing evidence-storage service and its private bucket configuration.
- Do not expose the media directory or object bucket publicly.

## Important limitations / next implementation slices

1. This is a persistent discussion feed, not realtime WebSocket chat yet.
2. Only JPEG and PNG photos are supported; video attachments are not included in this phase.
3. Community directory entries must be loaded from authoritative geographic sources. The feature does not fabricate ward or community names.
4. Community posts are available to authenticated users; a formal community membership/join model and member-specific posting controls are still needed.
5. Add conversion from a discussion post into a formal report, with the citizen confirming report category and incident location.
6. Add community-level moderation queues, reporting/flagging, rate limits, spam controls, and moderation appeals.
7. Add notification preferences for community announcements and replies.
8. Add realtime updates after the persistent feed and access controls are stable.

## Validation

Backend tests are in `backend/tests/test_community_spaces.py`. GitHub Actions on PR #79 must pass before merge. Validate image storage and restore behaviour against the target production object-storage configuration before public rollout.
