# Iteration 1 — engineer evidence

Date: 2026-10-19. Role: frontend software engineer. Scope: React/Vite frontend against centralized asynchronous mock service only. No backend, OpenAPI, API adapter, external issues or deployment created by this role.

## Executed commands and results

- `npm install`: successful, installed 162 packages. Later `npm install -D prettier`: successful formatting dependency added.
- Initial `npm test`: failed 3/9. Two actual account invariant failures identified by independent QA; third test failure was missing cleanup of prior RTL renders. Added explicit cleanup hook. Preserved actual failure report in role communications; no passing result claimed at this point.
- Expanded `npm test` before B01 fix: failed 4/15, all four account role-transition invariant cases; both engineer and QA daily/UI journey tests passed.
- PM groomed B01 in `_docs/bugs.json`; independent QA defined rejection/state-preservation/association-clearing cases before fix. Engineer validates merged user state before mutation, requires valid viewer association and clears irrelevant client/assignment data on role transitions.
- After fix and language persistence, `npm test` initially exposed test localStorage leakage (new RU preference persisted between tests). Test harness resets storage before each case.
- `npm test`: 3 files, **16 tests passed**, exit 0. Actual RTL forms exercised: admin client/account creation and multi-marketer assignment; marketer campaign creation/daily result creation and same-day edit; viewer report-only navigation; EN/RU and empty period; currency selection and reversed period error. Unit/service cases cover role isolation, revocation, archive retention, weighted ratios, unavailable zero ratios, strict numbers/date checks and B01 role transitions.
- `npm run build`: TypeScript and Vite production build exit 0. After final component extraction rerun recorded by independent QA.
- `npx prettier --write`: source/service/styles/components/tests formatted. Extracted sidebar, agency settings and trend components.

Independent QA owns `_docs/evidence/iteration-1-qa.md` and final acceptance; this engineer does not close issues or assert independent approval.

## Limitations

No browser visual/responsive inspection was available; RTL/jsdom verifies actual React interactions but cannot prove browser layout. Google authentication handshake untested and not implemented in mock-only iteration. Default entrypoint intentionally shows mock preview until iteration5 replaces it with real service; never deploy this preview as production authentication. No real data persistence is claimed until SQLite iteration.
