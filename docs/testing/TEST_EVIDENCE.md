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
- **PR-triggered backend tests:** PASS — run [42714503207](https://github.com/cikwom/govconnectx/actions/runs/42714503207), on commit `18bae035fcfae0b60c896df4a6394658c37f3f91`.
- **PR-triggered frontend build:** PASS — run [42714503482](https://github.com/cikwom/govconnectx/actions/runs/42714503482), on the same commit.
- The only later changes before this evidence update were documentation-only. The latest documentation commit has new push checks running; the code and PR checks above passed.
- **Manual browser validation:** NOT RUN. Test department State/LGA scope changes, category routing, unassigned queue assignment, zone → State → LGA drill-down, citizen report creation from a different home State, and mobile/responsive layout.


## 2026-11-17 — Browser end-to-end coverage, citizen and admin workflows

### Citizen registration, sign-in and geographic reporting — PR #64
- **Repository:** `cikwom/govconnectx`
- **PR:** [#64](https://github.com/cikwom/govconnectx/pull/64) — merged.
- **Merged commit:** `04cf0380ab3cdb62a9018c98742339db7479b3ae`
- **Browser suite:** PASS — 2/2 Chromium tests on PR head `fde7ce28bea02d5698cddd8342b0b3a8389d8278`; the tests cover registration with State/LGA, sign-in, and citizen report submission with State/LGA/Ward/Community routing.
- **PR checks:** PASS — GovConnectX CI run [44169726628](https://github.com/cikwom/govconnectx/actions/runs/44169726628), backend tests run [44169726584](https://github.com/cikwom/govconnectx/actions/runs/44169726584), frontend build run [44169726590](https://github.com/cikwom/govconnectx/actions/runs/44169726590).
- **Post-merge checks:** PASS — GovConnectX CI run [44169909231](https://github.com/cikwom/govconnectx/actions/runs/44169909231), backend tests run [44169909282](https://github.com/cikwom/govconnectx/actions/runs/44169909282), frontend build run [44169909309](https://github.com/cikwom/govconnectx/actions/runs/44169909309).

### Administrator account lifecycle — PR #65
- **Repository:** `cikwom/govconnectx`
- **PR:** [#65](https://github.com/cikwom/govconnectx/pull/65) — merged.
- **Merged commit:** `54eca834a51b5cb4db005a89b5aa17acee96aa72`
- **Browser suite:** PASS — 3/3 Chromium tests on PR head `06f28ef8313d6765bbea9372c283b8fe4d3c947b`; the admin test covers suspend, reactivate and anonymize/delete with audit reasons, plus self-deletion protection.
- **PR checks:** PASS — GovConnectX CI run [44170371905](https://github.com/cikwom/govconnectx/actions/runs/44170371905), backend tests run [44170372166](https://github.com/cikwom/govconnectx/actions/runs/44170372166), frontend build run [44170371925](https://github.com/cikwom/govconnectx/actions/runs/44170371925).
- **Post-merge checks:** PASS — GovConnectX CI run [44170580188](https://github.com/cikwom/govconnectx/actions/runs/44170580188), backend tests run [44170580151](https://github.com/cikwom/govconnectx/actions/runs/44170580151), frontend build run [44170580343](https://github.com/cikwom/govconnectx/actions/runs/44170580343).

### Test scope and limitations
- Browser tests use deterministic mocked API responses and synthetic test identities. They validate frontend navigation, form interactions, and request payloads; they do not modify a live database or prove production API integration.
- **Live-backend browser regression:** NOT RUN.
- **Manual mobile, keyboard-only and screen-reader regression:** NOT RUN.
- **Production media upload/download and external email/SMS delivery:** NOT RUN.
- Automated accessibility source checks passed (22 checks) and translation coverage passed (544 keys); these do not replace a manual WCAG or native-speaker review.
- The frontend dependency audit blocks high-severity production dependencies and critical-severity findings across the full dependency tree. A newly disclosed high-severity `picomatch` build-tool advisory has no published fixed release in the advisory; it remains an upstream dependency risk to revisit when a fix is available.


## 2026-11-17 — Report detail actions and evidence upload — PR #67
- **Repository:** `cikwom/govconnectx`
- **PR:** [#67](https://github.com/cikwom/govconnectx/pull/67) — merged.
- **Merged commit:** `e1c567438da5f4dc56603854f884362af747eb5a`
- **Browser suite:** PASS — 4/4 Chromium tests on PR head `ab9e451c4a0d4b989f624e82bf02e6e66b25bfc9`. New report-detail test verifies duplicate guidance, synthetic PNG evidence upload, critical escalation payload, and resolved-report feedback payload.
- **PR checks:** PASS — GovConnectX CI run [44171424732](https://github.com/cikwom/govconnectx/actions/runs/44171424732), backend tests run [44171424509](https://github.com/cikwom/govconnectx/actions/runs/44171424509), frontend build run [44171424504](https://github.com/cikwom/govconnectx/actions/runs/44171424504).
- **Post-merge checks:** PASS — GovConnectX CI run [44171665891](https://github.com/cikwom/govconnectx/actions/runs/44171665891), backend tests run [44171665876](https://github.com/cikwom/govconnectx/actions/runs/44171665876), frontend build run [44171665997](https://github.com/cikwom/govconnectx/actions/runs/44171665997).
- **Limitations:** the report detail tests use mocked API fixtures and synthetic image bytes. They do not prove production storage, malware scanning, signed download URLs, or live database persistence. Those remain NOT RUN.


## 2026-11-17 — Agency operations dashboard — PR #69
- **PR:** [#69](https://github.com/cikwom/govconnectx/pull/69) — merged.
- **Merged commit:** `31207da4c2e5e345ca8b04e27002f30fe7ca460d`
- **Browser suite:** PASS — 6/6 Chromium tests. Covers the department report queue, field-officer assignment, status progression, and the individual field-officer view.
- **Translations/accessibility:** 569 interface keys covered in Hausa, Yorùbá and Igbo; 22 automated accessibility source checks passed.
- **PR checks:** PASS — GovConnectX CI [44175013940](https://github.com/cikwom/govconnectx/actions/runs/44175013940), backend tests [44175013801](https://github.com/cikwom/govconnectx/actions/runs/44175013801), frontend build [44175013826](https://github.com/cikwom/govconnectx/actions/runs/44175013826).
- **Post-merge checks:** PASS — GovConnectX CI [44175271456](https://github.com/cikwom/govconnectx/actions/runs/44175271456), backend tests [44175271156](https://github.com/cikwom/govconnectx/actions/runs/44175271156), frontend build [44175271151](https://github.com/cikwom/govconnectx/actions/runs/44175271151).

## 2026-11-17 — Private staff notes — PR #70
- **PR:** [#70](https://github.com/cikwom/govconnectx/pull/70) — merged.
- **Merged commit:** `d065dc33cca86784a1a1894c0ac95dece5a36056`
- **Browser suite:** PASS — 8/8 Chromium tests. Covers staff-only internal-note creation and verifies the citizen view does not receive the private-note control.
- **Backend privacy test:** Existing `test_internal_comments_hidden_from_citizens` passed in the backend suite; the API filters internal comments from citizen responses and rejects citizen attempts to create internal notes.
- **Translations/accessibility:** 572 interface keys covered in Hausa, Yorùbá and Igbo; 22 automated accessibility source checks passed.
- **PR checks:** PASS — GovConnectX CI [44178340205](https://github.com/cikwom/govconnectx/actions/runs/44178340205), backend tests [44178309011](https://github.com/cikwom/govconnectx/actions/runs/44178309011), frontend build [44178339909](https://github.com/cikwom/govconnectx/actions/runs/44178339909).
- **Post-merge checks:** PASS — GovConnectX CI [44178593088](https://github.com/cikwom/govconnectx/actions/runs/44178593088), backend tests [44178593163](https://github.com/cikwom/govconnectx/actions/runs/44178593163), frontend build [44178593112](https://github.com/cikwom/govconnectx/actions/runs/44178593112).

### Additional limitations
- Agency and internal-note browser tests use mocked API fixtures and synthetic identities. They validate navigation, role-specific UI and request payloads, not a live deployed API or production database.
- Internal notes are protected by the existing backend authorization and citizen comment filtering; production integration still requires a live-backend regression.
- Manual mobile, keyboard-only and screen-reader testing remains NOT RUN.
