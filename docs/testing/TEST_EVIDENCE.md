# Test evidence log

This is the factual run history. Keep unrun checks marked NOT RUN; update entries only after the test is performed.

## 2026-11-03 — Phase 6 pull request #6

- **Repository:** `cikwom/govconnectx`
- **Branch:** `feature/citizen-report-details-evidence-phase-6`
- **Commit tested:** `8704aefbff6a43bfb03760c6183319ce0749de3f`
- **PR:** https://github.com/cikwom/govconnectx/pull/6
- **PR state at checkpoint:** open, not merged; mergeable reported true.
- **Frontend build workflow:** PASS — run [41717048388](https://github.com/cikwom/govconnectx/actions/runs/41717048388). Workflow includes dependency audit, TypeScript check and production build.
- **Backend tests workflow:** PASS — run [41717048474](https://github.com/cikwom/govconnectx/actions/runs/41717048474).
- **Manual browser testing:** NOT RUN / awaiting local test by project owner.
- **Phase 6 scenarios still to execute:** report detail and ownership boundaries; public history; comment submit; JPEG/PNG/PDF upload; authenticated download; invalid/oversize upload; cross-citizen evidence denial.
- **Code review notes:** authenticated download URL cleanup is delayed by one second after initiating the browser download. This is a browser reliability improvement, not proof of manual download success.

## Manual run record template

Copy this section for each manual test session:

### YYYY-MM-DD — [phase / feature]
- Tester:
- Branch:
- Commit SHA:
- Environment (OS, browser, backend DB):
- Test checklist sections:
- PASS:
- FAIL:
- NOT RUN:
- Failure reproduction / logs:
- Follow-up issue or PR:

## 2026-11-09 — Geographical Zones Phase 2

- **Repository:** `cikwom/govconnectx`
- **Branch:** `feature/geographical-zones-phase-2`
- **Code commit tested:** `bb41ece401d2e99be26ac94964f9ef12798c96dc`
- **PR:** [#19](https://github.com/cikwom/govconnectx/pull/19) — draft, not merged.
- **Backend tests:** PASS — push workflow run [42714191059](https://github.com/cikwom/govconnectx/actions/runs/42714191059). The suite reported 55 tests; the later run at this revision included the geographic scope, routing and admin drill-down tests.
- **Frontend build:** PASS — push workflow run [42714191083](https://github.com/cikwom/govconnectx/actions/runs/42714191083), including TypeScript check, dependency audit and production build.
- **Earlier failure and correction:** the first frontend attempt exposed invalid escaped template literals in the new geographic panel; corrected before the passing `bb41ece4` run. Earlier backend failures exposed missing scope fixtures and a missing `department_id` in `ReportResponse`; corrected before the passing `bb41ece4` backend run.
- **PR-triggered checks:** subsequent PR checks were still running at the time this evidence entry was written; confirm the latest PR checks before merge.
- **Manual browser validation:** NOT RUN. Test department State/LGA scope changes, category routing, unassigned queue assignment, zone → State → LGA drill-down, citizen report creation from a different home State, and mobile/responsive layout.
