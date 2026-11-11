# Accessibility implementation and verification

**Status:** Accessibility foundations are implemented; formal WCAG 2.2 AA conformance has not been established.

## Changes in this batch

- Interactive controls have a 44 CSS-pixel minimum height to improve pointer and touch usability.
- Checkbox and radio controls have a 24 × 24 CSS-pixel target and use the application accent color.
- Keyboard focus remains visible, with a brighter focus outline in dark theme.
- High-contrast preference increases focus visibility and control/panel border weight.
- Windows High Contrast / forced-colors mode receives system-color focus and skip-link treatment.
- The document advertises the active light/dark color scheme to native controls.
- Existing skip navigation and reduced-motion support remain in place.

## Required manual verification before claiming WCAG 2.2 AA

- [ ] Complete every journey using keyboard only: landing page, registration, sign-in, citizen dashboard, report submission, report details, preferences, community services and all staff/admin workflows.
- [ ] Confirm focus order follows the visual and reading order; no keyboard traps; dialogs/menus (if present) open, close and return focus correctly.
- [ ] Confirm every input has a programmatic label, required state and associated error/help text; errors are announced and focus is moved appropriately when necessary.
- [ ] Test with a screen reader (NVDA + Firefox/Chrome on Windows; VoiceOver + Safari on Apple devices).
- [ ] Test at 200% and 400% zoom and at a 320 CSS-pixel viewport; content must reflow without two-dimensional scrolling except where essential.
- [ ] Verify text, controls, focus indicators and meaningful graphics against WCAG contrast requirements in both themes.
- [ ] Test Windows forced-colors/high-contrast mode and the operating-system reduced-motion preference.
- [ ] Check headings, landmarks, page titles, link purpose, button names, table headers and status announcements on every route.
- [ ] Check media alternatives, captions/transcripts and accessible upload feedback wherever evidence media is presented.
- [ ] Include keyboard and screen-reader testing with citizen, field-officer, department-admin and system-admin roles.

## Important limitations

- These CSS improvements are a foundation, not proof of conformance.
- Automated checks cannot replace manual keyboard, screen-reader, zoom/reflow and contrast testing.
- Legal and official text translations require competent review before being treated as authoritative.
- Record each issue with route, role, assistive technology/browser, reproduction steps and severity before closing the audit.
