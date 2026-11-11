# Localization and language support

GovConnectX currently offers English, Hausa, Yorùbá and Igbo interface choices. The language selector is available on public landing/sign-in/registration/transparency pages and inside the authenticated application. A selected language is remembered in the browser; authenticated users can save it with their account preferences.

## Current coverage in this implementation batch

The first expanded translation pass covers:
- Public landing-page navigation, headline, calls to action and feature explanations.
- Sign-in and registration screens, including the State/LGA home-area labels.
- Authenticated navigation and account preferences.
- Citizen dashboard, report submission form, incident categories and workflow statuses.
- Lost and Found notices and public service directory.
- Public transparency navigation and localized date formatting.

The dictionary uses English as the fallback whenever a key has not yet been translated. A translation completeness script checks every literal `t("...")` use in the frontend and the landing-page strings selected dynamically from its feature list.

## Deliberate limits

- This is a first-pass interface translation, not a certified translation.
- The agency/staff workflow panels, full System Admin Command Centre, report-detail history/comments, and some remaining operational screens still contain English text and require additional localization work.
- The Terms of Use and Privacy Notice remain in English in this batch. Legal text must not be machine-translated and published as authoritative without review by a qualified Nigerian legal/privacy reviewer and competent Hausa, Yorùbá and Igbo translators.
- Translations should be reviewed by native speakers familiar with civic administration, public safety and Nigerian local-government terminology before a public launch.

## Validation

Run from `frontend/`:

```powershell
npm.cmd run check:translations
npm.cmd run typecheck
npm.cmd run build
```

The translation check fails on duplicate dictionary keys or a literal UI translation key missing from Hausa, Yorùbá or Igbo. It is a coverage guard, not a linguistic quality assessment.
