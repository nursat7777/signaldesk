# Iteration 1 independent acceptance checklist

QA preparation only; no PASS implied. Environment permits RTL/jsdom, not browser/visual inspection. Real Google sign-in belongs to later integration and remains unverified here.

- Admin: create client in selected currency, archive without losing reports; approve user; associate viewer; assign multiple marketers; revoke access.
- Marketer: assigned clients only, new campaign fixed channel, daily create with all six metrics, date revisit loads existing version, save edits without duplicate.
- Viewer: one client only, no mutation controls, reports and filters remain available.
- Service: direct unauthorized calls forbidden; revoked enabled state/assignments checked live; stale update conflicts; invalid/future dates and invalid counts/money rejected; explicit zero allowed.
- Reports: inclusive date range, empty state, weighted ratios and unavailable denominators, per-client currency, archive retains reporting history.
- UI: EN/RU control, loading/empty/error state and form interactions, selected-client refresh, role switch refresh; no assertion of visual quality without browser execution.
- Reproducibility: executed automated tests and frontend production build; record exact counts and exit statuses after frontend declares ready.
