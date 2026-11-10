# Ward and Community Zoning — Handoff

**Repository:** `cikwom/govconnectx`  
**Branch:** `feature/ward-community-zoning`  
**Base:** `main` after PR #25 merge.

## Implemented

- Added `wards` and `communities` reference models.
- Added nullable `incident_ward_code` and `incident_community_code` to reports, with an existing-database migration.
- Added public lookup endpoints:
  - `GET /api/v1/locations/lgas/{lga_code}/wards`
  - `GET /api/v1/locations/wards/{ward_code}/communities`
- Added System Admin-only directory management:
  - `POST /api/v1/locations/admin/wards`
  - `POST /api/v1/locations/admin/communities`
- Report creation validates that a selected ward belongs to the selected LGA and a selected community belongs to the selected ward.
- Citizen report form supports optional ward/community selectors after State and LGA.
- System Admin Command Centre has a panel to add verified ward/community reference entries.
- Report details display the selected ward/community codes.

## Geographic data integrity

- No ward/community names or codes have been fabricated or preloaded.
- Administrators must enter codes and names from authoritative records supplied by INEC or the relevant state/local government.
- A report can still be submitted with State and LGA only when ward/community reference data is unavailable.
- Automatic department routing and jurisdiction enforcement remain at the existing State/LGA level. Ward/community are captured as more precise incident metadata in this batch; ward-specific department jurisdiction rules are a separate follow-on change.

## Validation status

No local backend tests, frontend typecheck/build or browser checks were run in this session. Check GitHub Actions and validate the migration on a copy of the current production database before deployment.

## Next

1. Add bulk import with duplicate detection and preview for authoritative ward/community datasets.
2. Add ward-level department jurisdiction scopes without weakening existing State/LGA access checks.
3. Add map boundary data only from licensed/authoritative geospatial sources.
4. Add tests for invalid ward/LGA and community/ward combinations.
