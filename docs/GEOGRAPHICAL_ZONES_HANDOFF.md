# Geographical zones and administrative areas

## Purpose

GovConnect Nigeria uses Nigeria's six geopolitical zones for high-level reporting, but operational queues are organised by state and Local Government Area (LGA). A geopolitical zone is not a substitute for an LGA assignment.

## Current implementation — Phase 1

- Reference directory contains 37 administrative state-level units (36 states plus the Federal Capital Territory) and 774 LGAs.
- Every state record carries its geopolitical zone.
- Public lookup endpoints:
  - `GET /api/v1/locations/states`
  - `GET /api/v1/locations/states/{state_code}/lgas`
- Public registration can optionally record a citizen's home state and LGA.
- Every report can optionally record its incident state and LGA independently of the citizen's home area.
- The API validates that an LGA belongs to the selected state.
- Existing accounts and historical reports remain valid because the new location fields are nullable.

## Data source and attribution

The reference directory is derived from **Open Admin Data — Nigeria Administrative Divisions**, CC BY 4.0:
https://github.com/open-admin-data/nigeria-administrative-divisions

The source dataset lists 37 state-level units and 774 LGAs. INEC's public state-office directory also describes 36 states, FCT, and 774 LGA offices:
https://www.inecnigeria.org/about/state-offices

This is a reference directory, not an official government partnership or an assertion that GovConnect is operated by INEC. Before public launch, verify names and boundaries against authoritative government sources and record any corrections with provenance.

## Next implementation steps

1. Add registration and report-form dependent State/LGA selectors.
2. Add administrator-managed geographic scopes for staff (one or more states/LGAs).
3. Enforce geographic scope in every staff report list, detail, assignment, status, attachment, history, and comment operation. Do not rely on frontend filters.
4. Route new reports to an LGA triage queue, then department/team queues; support an exception queue when no local team is configured.
5. Add ward-level data only after validating its completeness and authoritative source. Do not infer a ward from a map pin without a reliable boundary dataset.
6. Add national admin filters and drill-down: geopolitical zone → state → LGA.
7. Complete privacy review for home-area and incident-location collection, visibility, retention, and access logging.

## Privacy and access rules

- A citizen's home area is private profile information and must not be shown in public report views.
- Report routing uses the incident location, not the citizen's home location.
- Citizens may report incidents outside their home LGA.
- Location fields are nullable during rollout to preserve existing accounts and historical data.
- Geographic scope must be enforced server-side before staff access is narrowed by area.

## Phase 2 implementation checkpoint — 9 November 2026

Implemented on `feature/geographical-zones-phase-2` (draft PR #19):

- Departments can be assigned whole-State or LGA-level geographic scopes by a system administrator.
- Departments can be configured for incident categories.
- Staff report lists/details and all detail operations that call the shared report authorization helper are restricted to the department's geographic scope.
- Assignment requires the destination department to cover the incident State/LGA.
- New reports auto-route only when exactly one active department matches both category and incident geography. Zero or multiple matches remain in the national unassigned triage queue.
- Admin APIs expose unassigned reports and aggregate counts from geopolitical zone → State → LGA.

API additions:
- `GET/PUT /api/v1/departments/{department_id}/geographic-scopes`
- `GET/PUT /api/v1/departments/{department_id}/routing-categories`
- `GET /api/v1/admin/reports/unassigned`
- `GET /api/v1/admin/geography/overview`

Important: the Admin UI for scope/category management, triage and geographic drill-down is not yet connected. GPS-vs-selected-location review is also pending. Keep PR #19 as draft and do not merge until CI passes and the UI/manual checks are complete.

Resume using the Phase 2 commands in the root README. Citizen home location remains private and is never used for routing.
