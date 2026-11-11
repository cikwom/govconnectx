# Durable notification outbox

## How delivery works

Report auto-routing, assignment, status changes and escalations now create durable delivery rows for each channel the recipient has enabled.

- Email delivery is created only when email notifications are enabled (or no preference record exists).
- SMS delivery is created only when the account is active, the number is verified, SMS is enabled, and consent has not been revoked.
- SMS text contains a short event notice and directs the user to sign in; report titles and user-submitted content are not copied into SMS.
- A FastAPI background task attempts each new delivery after the request transaction completes.
- Failed deliveries remain in the database and are retried by the separate worker.
- Retry schedule is bounded: 30, 60, 120 and 240 seconds after the first failure; after five total attempts the row becomes `failed`.
- A delivery left in `sending` for more than five minutes is considered abandoned and can be reclaimed by the worker.
- Provider failures store a generic error string; credentials, message bodies and full destination addresses are not returned by the admin monitoring endpoint.

## Run locally

Start the API as usual, then start the worker from a second terminal:

```powershell
cd C:\\Users\\gentle\\govconnectx\\backend
.\\.venv\\Scripts\\python.exe -m app.workers.notification_worker
```

The worker uses the same `DATABASE_URL`, SMTP and Termii environment variables as the API. Optional tuning:

- `NOTIFICATION_WORKER_POLL_SECONDS=15`
- `NOTIFICATION_WORKER_BATCH_SIZE=25` (maximum 100)

## Render deployment

Create a **Background Worker** for this repository, using the same backend runtime and environment variables as the API service.

- Build command: `pip install -r requirements.txt`
- Start command: `python -m app.workers.notification_worker`
- Set `DATABASE_URL`, `JWT_SECRET`, SMTP settings and Termii settings in the worker's secret environment.
- Set the same database URL on the API and worker.
- Start with one worker instance. The row-claiming transaction uses database row locks on PostgreSQL; test concurrency before increasing worker count.

The API process still makes the first delivery attempt, so new deliveries can be attempted even before the separate worker is deployed. The worker is required for scheduled retries and recovery of abandoned claims.

## Monitoring

System Administrators can view `GET /api/v1/admin/notification-deliveries` from the Command Centre. The endpoint shows counts by channel/status and recent attempts with masked destinations; it does not expose message bodies or full recipient addresses.

Supported filters: `status=queued|sending|sent|failed`, `channel=email|sms`, and `limit=1..100`.

## Delivery semantics and limitations

- This is an at-least-once delivery design. A process crash after a provider accepts a message but before the database records success can cause a duplicate on recovery.
- A provider returning success means it accepted the request, not that the recipient handset or mailbox received it.
- Provider delivery receipts/webhooks, permanent-failure classification, dead-letter review and a user-facing delivery history are not included yet.
- Retention/cleanup policy for delivery rows must be defined before long-running production use.
- Do not rely on SMS or email for emergency dispatch.
