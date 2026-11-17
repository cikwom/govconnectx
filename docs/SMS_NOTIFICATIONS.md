# SMS notifications and phone verification

## Delivery provider

GovConnectX uses Termii's Nigerian SMS API. Configure these variables in the backend API and notification-worker environments:

- `TERMII_API_KEY`: private Termii API key
- `TERMII_SENDER_ID`: approved sender ID
- `TERMII_API_URL`: defaults to `https://api.ng.termii.com/api/sms/send`
- `SMS_TIMEOUT_SECONDS`: HTTP request timeout; defaults to 10 seconds

Never expose the API key through a `VITE_*` frontend variable or commit it to Git. If the provider key or sender ID is missing, delivery fails safely and the outbox records a retryable failure. Configure the same provider credentials for the API and the separate worker.

## User verification and consent

1. A signed-in user enters a phone number in international E.164 format, for example `+2348012345678`.
2. GovConnectX sends a six-digit one-time code through Termii.
3. The code is stored as a keyed HMAC digest, expires after 10 minutes, and is limited to five verification attempts. Requests are rate-limited to one per minute and five per hour per account and per phone number.
4. A phone number cannot be verified on multiple accounts.
5. Verifying a number does **not** enable SMS. The user must separately enable the SMS notification preference.
6. Changing a phone number clears verification and requires fresh consent for the new number.
7. Turning SMS off records a revocation timestamp. The durable queue checks that the account is active, the phone is verified, SMS is enabled, consent is recorded and consent has not been revoked before creating a delivery.

The current account profile stores one phone number per user. Phone numbers are unique. Verification codes are never returned by the API or written to application logs.

## API

- `POST /api/v1/preferences/phone/request-verification` — authenticated; JSON body `{"phone_number":"+2348012345678"}`
- `POST /api/v1/preferences/phone/verify` — authenticated; JSON body `{"code":"123456"}`
- `GET /api/v1/preferences` — returns phone verification and SMS consent state.
- `PUT /api/v1/preferences` — includes `sms_notifications`; enabling it before phone verification returns HTTP 400.

## Durable delivery, retries and monitoring

Report routing, assignment, status changes and escalations enqueue durable notification-delivery rows. SMS is queued only for an active user with a verified phone number and current explicit consent. SMS bodies contain a short event notice and a sign-in prompt; report titles and user-submitted content are not copied into SMS.

The API makes an initial delivery attempt and the separate notification worker retries due rows. The retry schedule is bounded (30, 60, 120 and 240 seconds after successive failures); after five total attempts the row is marked failed. A delivery left in `sending` for more than five minutes can be reclaimed. System Administrators can inspect channel/status counts and recent attempts in the Command Centre; destination numbers are masked and message bodies are not exposed.

Start the worker locally from the backend directory:

```powershell
.\.venv\Scripts\python.exe -m app.workers.notification_worker
```

In production, deploy a separate background worker with the same `DATABASE_URL`, Termii and relevant application secrets as the API. See [NOTIFICATION_OUTBOX.md](NOTIFICATION_OUTBOX.md) for worker configuration and operational details.

## Delivery limitations and launch requirements

- A successful Termii response means the provider accepted the request; it does not prove that the handset received or displayed the message.
- The current adapter does not implement provider delivery-receipt webhooks, permanent-failure classification or exactly-once delivery. A crash after provider acceptance but before database acknowledgement can result in a duplicate on retry.
- Configure an approved Termii sender ID and valid API key before testing real delivery. Use a provider test account or controlled number and monitor provider spend.
- SMS is optional and must not be used for emergency dispatch or as the sole channel for urgent safety instructions.
- Before launch, verify opt-in and opt-out from the actual UI, provider acceptance on a controlled number, worker retry after a simulated failure, masked admin monitoring, and the worker's restart/recovery behavior.
- Have the Privacy Notice reviewed by qualified Nigerian privacy counsel to cover phone-number processing, verification, SMS consent, provider sharing, retention and user rights. Native-speaker and legal review are separate release requirements.
