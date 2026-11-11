# GovConnectX authentication and account security

## Sign-in areas

- Citizens use `/login`.
- Authorised government and administration users use `/admin/login`.
- Both routes use the same backend authentication endpoint. The government sign-in screen rejects citizen roles before storing an access token.
- Public registration always creates a citizen account. System administrator roles must be provisioned by an authorised platform administrator.

## Password recovery

The public recovery request is `POST /api/v1/auth/password-reset/request` with an email address. The API returns the same response whether or not the account exists. If an active account matches, the backend sends a one-time link to its registered email.

The link points to `/reset-password?token=...` on the configured frontend and expires after 30 minutes. Only a SHA-256 hash of the random token is stored. A successful reset consumes the token, invalidates other outstanding reset tokens, changes the password and increments the account token version so existing access tokens stop working.

The SMTP sender is the existing `send_notification_email` service. Password recovery and security alerts are security messages and do not depend on the user's optional notification preferences.

## Required deployment configuration

Set these backend environment variables in Render (and locally in `backend/.env`):

- `FRONTEND_URL`: public frontend origin, e.g. `https://your-frontend.onrender.com` or your verified GovConnect domain. Do not include a trailing slash.
- `SMTP_HOST`
- `SMTP_PORT` (usually 587 for STARTTLS)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`

Keep SMTP credentials and all other secrets out of Git. The repository's `.env.example` contains placeholders only.

If SMTP is not configured or delivery fails, the API still returns a generic recovery response; the user will not receive the link. Confirm the SMTP provider's sender/domain verification and check server logs and delivery monitoring before announcing recovery as operational.

## Sign-in history and session revocation

Successful sign-ins, password resets and session-revocation actions are recorded in `auth_security_events`. Authenticated users can view their recent activity at `GET /api/v1/auth/security/activity` and revoke all existing sessions at `POST /api/v1/auth/security/revoke-sessions`.

The current activity record stores the request IP address and user-agent string. It does not claim precise geolocation. A session revocation increments the account token version, invalidating all previously issued access tokens; the user must sign in again.

## Administrator account recovery operations

Administrators use the same one-time email recovery flow. If an administrator has also lost access to the registered work email, do not create a public bypass, shared password, or direct database password edit. Recovery must be handled by the designated platform owner after independently verifying the administrator's identity and authority, with the action recorded in the organisation's operational audit process.

Before production launch, add a separately verified second factor for privileged-account recovery (for example, an enrolled authenticator or verified phone) and a documented two-person break-glass process for the case where the sole administrator loses both factors. The current implementation provides email-based recovery and global session revocation; it does not yet provide that second factor or an administrator recovery approval workflow.
