# GovConnectX Accountability Engine — Product Roadmap

**Repository:** https://github.com/cikwom/govconnectx  
**Implementation branch:** `feature/accountability-engine-expansion`  
**Base:** `main` at the Phase 2 geographic-zones merge  
**Product direction:** A civic engagement and public-service accountability platform for Nigeria.

This roadmap expands the existing application. It is not permission to expose private citizen reports, GPS coordinates, evidence, or personal data publicly. Backend authorization remains authoritative.

## Existing capabilities to preserve

- Citizen registration, login, and role-based protected routes.
- Report submission, detail, status history, comments, and notifications.
- Department assignment, SLA tracking, and administrative command centre.
- Nigerian state/LGA directory and department geographic jurisdictions.
- Automatic report routing by category and geographic scope, with national unassigned triage.
- Consent-based GPS sharing and administrator location review.
- Private evidence upload/download in development. Production uploads remain disabled until durable private object storage, backups, and malware scanning are configured.
- Public landing page, light/dark theme, Terms of Use, and Privacy Notice.

## Feature inventory and delivery plan

| Capability | Planned outcome | Delivery / dependency |
|---|---|---|
| Government intelligence dashboard | National, state, LGA, department and SLA analytics | Extend existing admin overview and geographic drilldown |
| Geographic zoning | State, LGA, ward and community boundaries | State/LGA and department scope exist; ward/community authoritative directory remains |
| Citizen reporting | Photo/video, GPS, category, location and progress tracking | Core reporting/GPS exists; production media storage gate remains |
| Accountability workflow | Reference numbers, routing, officer assignment, deadlines, resolution evidence | Core assignment/status/SLA exists; add verification and stronger tracking UX |
| Agency and department portals | Role-specific views for state/LGA/department staff and field officers | Existing staff roles/departments; jurisdiction and portal UX expansion |
| Public transparency | Privacy-safe aggregate reports, resolution and service metrics | Initial aggregate API added in this branch |
| Notifications | In-app and email first; SMS/push as configured channels | In-app exists; provider delivery and preferences remain |
| Audit trail | Read-only append-only event history for sensitive actions | Initial event model and protected read API added in this branch; broaden coverage and add tamper-evident retention controls |
| Duplicate report detection | Similarity hints and linked cases for human review | Planned; never auto-reject based only on similarity |
| Emergency escalation | Urgency triage, escalation path and clear emergency guidance | Planned; must not imply emergency dispatch or guaranteed response |
| Community feedback | Citizen feedback after resolution, moderation and aggregate satisfaction | Planned |
| Lost and Found | Moderated reports for lost/recovered property | Planned; protect contact and identity details |
| Government service directory | Verified public service listings, eligibility, contact and office locations | Planned; data ownership and verification process required |
| Multilingual support | English, Hausa, Yoruba and Igbo interface/content | Planned; professional translation and language QA required |
| Accessibility | Keyboard navigation, screen-reader labels, contrast, scalable text | Continuous requirement; formal WCAG 2.2 AA review planned |
| Performance analytics | Department workload, response time, resolution rates and overdue cases | Existing SLA base; add fair denominators and contextual reporting |
| Production readiness | Managed database, private object storage, backups, malware scanning, rate limits, monitoring, retention and incident response | Required before production launch |

## Delivery order

### Workstream A — Accountability and transparency foundation
1. Persist report lifecycle audit events in the same transaction as the action.
2. Expose audit events only to System Admins, with pagination and filters.
3. Publish aggregate transparency statistics without citizen identifiers, descriptions, exact coordinates, comments, or evidence.
4. Add regression tests for authorization, aggregation and audit recording.

### Workstream B — Government operations
1. Complete department and agency management, including verified ownership and geographic scope.
2. Add official assignment queues, workload, deadlines, escalation and resolution evidence.
3. Extend dashboards with state/LGA/department filters and reliable performance definitions.
4. Add report verification and citizen feedback.

### Workstream C — Citizen services
1. Add duplicate suggestions and linked cases with human review.
2. Add emergency escalation with explicit service limitations.
3. Add Lost and Found and a verified government service directory.
4. Add notification preferences and configured email/SMS/push providers.
5. Add reviewed translations and accessibility improvements.

### Workstream D — Launch readiness
1. Configure managed PostgreSQL (Neon or another selected provider) and migrations.
2. Configure durable private object storage, malware scanning, backups and retention.
3. Complete security, privacy, legal, accessibility and load testing.
4. Configure monitoring, incident response, rate limits and deployment rollback.

## Safety, privacy and governance rules

- Citizens may report issues inside or outside their home zone; routing follows the incident location and verified department jurisdiction.
- Ambiguous or unmatched routing goes to national triage, not an arbitrary department.
- Duplicate, high-volume or unusual activity indicators are review signals, not proof of abuse.
- Public transparency is aggregate-only. Suppress small geographic/category groups to reduce re-identification risk.
- GPS sharing must remain consent-based; citizen-selected incident location must not be silently overwritten.
- Only authorized staff may see private evidence and internal comments.
- Resolution requires a recorded action and, where appropriate, human verification; do not fabricate completed work.
- GovConnectX must not claim to be a government agency or government-endorsed service without formal authorization.
- Do not represent the platform as an emergency dispatch service unless an operational agreement and staffed response process exist.

## Current branch checkpoint

- Branch: `feature/accountability-engine-expansion`
- Base branch: `main`
- This branch introduces an audit event model, report lifecycle audit writes, a System Admin-only audit log endpoint, and a public aggregate transparency endpoint.
- CI and local integration tests must pass before a pull request is merged.
- Remaining capabilities in the inventory are planned work, not claims of completed functionality.
