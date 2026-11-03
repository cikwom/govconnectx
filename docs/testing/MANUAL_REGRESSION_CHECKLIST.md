# Manual regression checklist

Use these repeatable checks during development and before merging. Use synthetic accounts and test data only. Record date, tester, branch and exact commit SHA in `TEST_EVIDENCE.md`. Mark each check PASS / FAIL / NOT RUN; do not infer a pass.

## A. Startup and navigation
- [ ] Backend starts with documented environment and dependencies.
- [ ] Frontend starts at `http://localhost:5173`; API docs at `http://localhost:8000/docs`.
- [ ] API requests use configured `VITE_API_URL` and `/api/v1`.
- [ ] No uncaught browser-console errors during normal navigation.
- [ ] Protected-page refresh restores a valid session or redirects safely.

## B. Authentication and session
- [ ] Valid citizen registration and login work.
- [ ] Duplicate/invalid registration and incorrect credentials are rejected safely.
- [ ] Session restoration works while token is valid.
- [ ] Logout clears the session; protected pages require login.
- [ ] Expired/invalid token returns user to unauthenticated state.
- [ ] Citizen cannot self-assign a privileged role.

## C. Citizen report lifecycle
- [ ] Citizen submits report with title, description, category and coordinates.
- [ ] Missing required fields and invalid coordinates are rejected.
- [ ] Citizen dashboard lists only their own reports.
- [ ] Dashboard link opens matching report detail page.
- [ ] Detail shows correct metadata, status, location and SLA due date.
- [ ] Invalid/nonexistent IDs show safe error and working navigation.
- [ ] Changing URL/API IDs cannot expose another citizen's report, history, comments or evidence.

## D. Status history and comments
- [ ] Public status history is chronological; empty state is clear.
- [ ] Citizen submits non-empty public comment; it appears once and persists after reload.
- [ ] Empty/whitespace-only comments are rejected.
- [ ] Citizen cannot read or create staff-only internal comments.
- [ ] Failures are visible and do not silently discard user input.

## E. Evidence
- [ ] Valid JPEG, PNG and PDF upload and appear in the evidence list.
- [ ] Authenticated download returns the correct original file.
- [ ] Oversize, unsupported, empty and mismatched-content files are rejected by backend.
- [ ] Unauthenticated and cross-citizen evidence access is denied.
- [ ] Permitted staff access follows backend report authorization.
- [ ] Failed upload/download displays a useful error; attachments persist after refresh.
- [ ] Evidence storage is private and not exposed as public static files.

## F. Staff workflow and access
- [ ] Officials see only assigned reports; department staff see only permitted department reports.
- [ ] Authorized assignment to active staff in the correct department succeeds.
- [ ] Invalid, inactive or cross-department assignment is rejected.
- [ ] Valid status transitions succeed; invalid transitions are rejected.
- [ ] Reopening resolved/rejected report resets resolution time and SLA as specified.

## G. Notifications and SLA
- [ ] Assignment/status changes notify correct recipients.
- [ ] Users see only their own notifications.
- [ ] Unread count, mark-one-read and mark-all-read work.
- [ ] SLA summaries are role/department scoped and counts match test records.

## H. Admin and security
- [ ] Only authorized system admins perform system-wide admin actions.
- [ ] Users cannot elevate their own role through request payloads.
- [ ] API authentication and authorization failures are safe (401/403/404 per policy).
- [ ] CORS uses configured origins; production does not use wildcard origins.
- [ ] No secrets, tokens, password hashes or private evidence are exposed.
- [ ] Production has HTTPS, strong secrets, backups and durable private evidence storage.

## I. Simple citizen experience (Phase 7)
- [ ] Login and registration show only necessary fields and clear recovery links.
- [ ] Citizen home has obvious actions: Report an issue, My reports/Track, Lost something, Found something, Get help.
- [ ] A first-time user can find how to submit an issue without instruction.
- [ ] Report submission asks only for necessary details; photo is optional.
- [ ] Success screen shows a reference number and a simple tracking link.
- [ ] Mobile layout works at narrow screen sizes; controls are readable and accessible.
- [ ] Citizens do not see staff queues, SLA jargon or admin controls.

## J. Nationwide Lost & Found (Phase 8)
- [ ] User can create lost-item and found-item reports with category, description, state/LGA/location and approximate date.
- [ ] Search can find candidate items across state boundaries.
- [ ] Match suggestions are clearly labelled as possible matches, not confirmed identity.
- [ ] Sensitive identifying details and private contact information are never public.
- [ ] Owner proves possession/ownership using private details not displayed in listing.
- [ ] Finder can arrange handover through safe public collection guidance.
- [ ] Item status progresses through open, possible match, verified, returned/closed or safely cancelled.
- [ ] Users can report suspicious listings, scams or harassment; moderators can review abuse.
- [ ] No payment is required to claim property through the platform.
- [ ] Test cases cover false matches, duplicate listings, malicious claims and cross-state results.

## Phase completion
### Phase 6 — report details and evidence
- [ ] Sections A, C, D and E pass.
- [ ] Frontend and backend CI pass on exact PR head.
- [ ] Manual evidence recorded in `TEST_EVIDENCE.md`.

### Phase 7 — simple citizen experience
- [ ] Section I passes for desktop and mobile.
- [ ] Existing citizen report flows remain functional.

### Phase 8 — Lost & Found
- [ ] Section J passes, including privacy, authorization, abuse and cross-state tests.
- [ ] Matching is advisory; handover requires ownership verification.

### Official/department dashboards
- [ ] Sections F, G and H pass with separate synthetic citizen, official, department admin, supervisor and system admin accounts.
- [ ] Every staff action is authorized by backend policy, not merely hidden in UI.
