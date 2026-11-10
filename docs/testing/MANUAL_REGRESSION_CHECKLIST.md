# Manual regression checklist

Use this checklist for local integration testing and repeat it after changes to authentication, reports, workflow, notifications, evidence, or role permissions.

**Environment:** local development unless a test record explicitly says otherwise.  
**Test data:** use synthetic accounts and reports only.  
**Result values:** PASS / FAIL / NOT RUN. Add date, tester, branch and commit in `TEST_EVIDENCE.md`.

## A. Startup and basic navigation

- [ ] Backend starts with the documented environment and dependencies.
- [ ] Frontend starts at `http://localhost:5173`.
- [ ] API docs load at `http://localhost:8000/docs`.
- [ ] Frontend API requests target the configured `VITE_API_URL` and `/api/v1` prefix.
- [ ] Browser console has no uncaught errors during normal navigation.
- [ ] Refreshing a protected page restores a valid session or redirects safely to login.

## B. Authentication and session

- [ ] Register a new citizen using valid details.
- [ ] Duplicate/invalid registration is rejected with a useful message.
- [ ] Correct credentials log in and open the citizen dashboard.
- [ ] Incorrect credentials are rejected without exposing sensitive details.
- [ ] Reloading the page restores the session while the token is valid.
- [ ] Logging out clears the session and protected pages require login.
- [ ] Expired/invalid token responses return the user to an unauthenticated state.
- [ ] Citizen registration cannot self-assign a privileged role.

## C. Citizen report lifecycle

- [ ] Citizen submits a report with title, description, category and coordinates.
- [ ] Required-field and invalid-coordinate cases are rejected.
- [ ] Citizen dashboard lists only that citizen's reports.
- [ ] Dashboard report link opens the matching `/reports/:reportId` page.
- [ ] Detail page displays the correct report metadata, status, location and SLA due date.
- [ ] Invalid/nonexistent report IDs show a safe error and a working dashboard link.
- [ ] A citizen cannot open another citizen's report, history, comments or evidence by changing the URL/API ID.

## D. Status history and comments

- [ ] Detail page displays public status history in chronological order.
- [ ] Empty history and empty comments show sensible empty states.
- [ ] Citizen can submit a non-empty public comment.
- [ ] Empty/whitespace-only comments cannot be submitted.
- [ ] Comment appears once after submission and remains after reload.
- [ ] Citizen cannot create or read staff-only internal comments.
- [ ] Comment submission failures are visible and do not silently discard text.

## E. Evidence upload and download

- [ ] Upload a valid small JPEG.
- [ ] Upload a valid small PNG.
- [ ] Upload a valid small PDF.
- [ ] Uploaded file appears in the evidence list with filename, size and timestamp.
- [ ] Download each uploaded file and verify it opens and matches the original.
- [ ] Reject files larger than the configured 10 MiB default limit.
- [ ] Reject unsupported file extensions/types.
- [ ] Reject mismatched extension/content and invalid file signatures at the API.
- [ ] Empty files are rejected.
- [ ] Unauthenticated users cannot upload, list or download evidence.
- [ ] A different citizen cannot list or download another citizen's evidence.
- [ ] Authorized department staff/assigned officials can access only reports permitted by backend policy.
- [ ] Failed upload/download shows an error and leaves the page usable.
- [ ] Refreshing the report detail page still lists persisted attachments.

## F. Staff workflow and access boundaries

- [ ] Official sees only reports assigned to that official.
- [ ] Department admin/supervisor sees reports in their department.
- [ ] Staff cannot read reports outside their permitted department/assignment scope.
- [ ] Authorized staff can assign a report to an active staff member in the correct department.
- [ ] Invalid/inactive/cross-department assignees are rejected.
- [ ] Valid status transitions succeed.
- [ ] Invalid status transitions are rejected.
- [ ] Reopening a resolved/rejected report clears resolution time and restarts the SLA deadline.

## G. Notifications and SLA

- [ ] Assignment creates the expected notification for the report owner and assignee.
- [ ] Status changes notify the appropriate recipients.
- [ ] Users see only their own notifications.
- [ ] Unread count matches unread notifications.
- [ ] Mark-one-read and mark-all-read work.
- [ ] SLA summary is scoped to the caller's permitted role/department.
- [ ] Active, overdue, due-soon and missing-deadline counts match test records.

## H. Admin and security checks

- [ ] Only authorized system admins can perform system-wide role/admin operations.
- [ ] Users cannot elevate their own role through request payloads.
- [ ] API returns 401 for missing/invalid authentication and 403/404 for forbidden resources according to endpoint policy.
- [ ] CORS permits configured frontend origins and does not use wildcard origins in production.
- [ ] No secret, token, password hash or private file content is exposed in frontend logs or public responses.
- [ ] Evidence storage is not served as a public static directory.
- [ ] Production configuration uses HTTPS, strong secrets, durable private evidence storage and backups before real users are onboarded.

## Phase-specific completion

### Phase 6 — citizen report details and evidence

- [ ] Sections A, C, D and E pass.
- [ ] Phase 6 frontend/backend CI passes on the exact PR head.
- [ ] Manual result is recorded in `TEST_EVIDENCE.md`.

### Phase 7 — official and department dashboards

- [ ] Sections A, F and relevant parts of G/H pass.
- [ ] Citizen, official, department admin, supervisor and system admin views are tested with separate synthetic accounts.
- [ ] Every staff action is authorized by the backend, not only hidden in the UI.


## GPS incident-location review

- [ ] Submit a report after granting browser location permission over HTTPS; confirm GPS values are captured and both coordinate fields are populated.
- [ ] Submit a report after denying permission; confirm manual coordinates still work and GPS status is `not_provided`.
- [ ] Confirm selecting GPS does not alter the incident State or LGA.
- [ ] As System Admin, open the Incident GPS verification panel and confirm pending reports show coordinates and selected State/LGA.
- [ ] Confirm citizen and department accounts cannot access the admin review endpoints.
- [ ] Mark a report consistent, flag a mismatch, and mark another unable to verify; confirm reviewer and timestamp are recorded.
- [ ] Confirm a mismatch never rewrites the report's selected State/LGA or changes department routing.
- [ ] Confirm reports with no GPS remain available to the normal workflow.
