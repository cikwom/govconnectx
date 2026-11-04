# System Admin Command Centre — Handoff

## Purpose
Provide the GovConnectX System Admin with a protected operational view of platform users, citizen reports and recorded activity.

## Implemented endpoints
- `GET /api/v1/admin/overview` — user counts, role counts, report status counts, open and overdue totals.
- `GET /api/v1/admin/users` — searchable/paginated directory with account state and number of reports submitted.
- `GET /api/v1/admin/reports` — searchable report list including reporter name/email and report description.
- `GET /api/v1/admin/activity` — recent account registrations, report status events and assignments.

All endpoints use `require_roles("system_admin")`. User responses are explicitly shaped and do not include password hashes.

## Frontend
- Route: `/admin`.
- Navigation appears only for a System Admin.
- The page has platform summary cards, role/status breakdowns, user search, report search and an activity feed.
- Backend remains the authority: hiding the link is not treated as access control.

## Current limitations and next iteration
- Activity is reconstructed from registration timestamps, report status history and assignment records. It is not yet a complete immutable audit log.
- Add first-class audit events for comments, login events, role changes, account activation/deactivation and admin actions.
- Add carefully guarded role/account management, department administration, date filters, exports and optional live refresh.
- Do not implement keystroke tracking, private-message inspection or off-platform surveillance. The goal is accountability for recorded actions inside GovConnectX.
- Run CI and manual role-based regression before merge; no passing test result is claimed in this handoff.

## Local verification
1. Start backend with `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`.
2. Start frontend with `npm.cmd run dev` from `frontend`.
3. Sign in using the System Admin account and visit `http://localhost:5173/admin`.
4. Confirm citizen credentials cannot access the admin API (403) or admin page.
