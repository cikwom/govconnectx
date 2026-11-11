# SMS notifications and phone verification

## Delivery provider

The current SMS adapter uses Termii's Nigerian SMS API. Configure these variables in the backend service environment (for example, Render):

- `TERMII_API_KEY`: private Termii API key
- `TERMII_SENDER_ID`: approved sender ID
- `TERMII_API_URL`: defaults to `https://api.ng.termii.com/api/sms/send`
- `SMS_TIMEOUT_SECONDS`: HTTP request timeout; defaults to 10 seconds

Never expose the API key through a `VITE_*` frontend variable or commit it to Git. SMS delivery safely returns unavailable when the provider key or sender ID is missing.

## User verification and consent

1. A signed-in user enters a phone number in international E.164 format, for example `+2348012345678`.
2. GovConnect sends a six-digit one-time code through Termii.
3. The code is stored as a keyed HMAC digest, expires after 10 minutes, and is limited to five verification attempts. Requests are rate-limited to one per minute and five per hour per account and per phone number.
4. A phone number cannot be verified on multiple accounts.
5. Verifying a number does **not** enable SMS. The user must separately enable the SMS notification preference.
6. Changing a phone number clears verification and revokes the previous SMS consent for the new number.
7. Turning SMS off records a revocation timestamp. Notification delivery checks active account status, verified phone, enabled preference, consent timestamp and absence of revocation before queueing a message.

The current account profile stores one phone number per user. Phone numbers are unique. Verification codes are never returned by the API or written to application logs.

## API

- `POST /api/v1/preferences/phone/request-verification` — authenticated; JSON body `{"phone_number":"+2348012345678"}`
- `POST /api/v1/preferences/phone/verify` — authenticated; JSON body `{"code":"123456"}`
- `GET /api/v1/preferences` — returns phone verification and SMS consent state.
- `PUT /api/v1/preferences` — includes `sms_notifications`; enabling it before phone verification returns HTTP 400.

## Delivery behavior and limitations

- SMS is added to the same FastAPI background-task mechanism used by email notifications. A provider failure is logged without exposing message content or secrets; this first iteration does not yet have a durable delivery outbox, delivery receipts, retry scheduling or provider-status dashboard.
- Do not promise guaranteed delivery. A successful provider acceptance is not proof that a handset received the SMS.
- Configure an approved Termii sender ID and valid API key before testing real delivery. Use a provider test account/controlled number and monitor provider spend.
- SMS is optional and must not be used for emergency dispatch or as the sole channel for urgent safety instructions.
- Have the Privacy Notice reviewed by qualified Nigerian privacy counsel before public rollout to cover phone-number processing, verification, SMS consent, provider sharing, retention and user rights.
