# Iteration 1 independent QA — mock frontend

Date: 2026-10-19. Reviewer: separate QA agent, not frontend implementer. Reviewed local staged M02–M05 and genuine B01. GitHub URLs: none, publication pending. Revision: working tree following documentation commit 4a06645; frontend not committed at review time.

Verdict: PASS for the mock frontend iteration gate after B01 fix. This does not certify full MVP completion, backend persistence, external GitHub workflow, browser visual quality or live Google OAuth.

## Executed evidence

From frontend directory:

- Initial `npm test -- --run src/qa.service.test.ts`: exit 1; 5 passed, 2 failed. Invalid role/client account updates resolved instead of rejecting. Recorded B01, PM groomed, QA added transition and rollback regressions, frontend engineer fixed merged validation.
- Final `npm test` after engineer declared no further application edits: exit 0; Vitest 3.2.7, 3 files passed, 16 tests passed, start 17:01:01 runtime clock. Includes 13 independently authored QA tests and 3 engineer tests.
- Final `npm run build`: exit 0; TypeScript build plus Vite 6.4.4, 1584 modules, generated dist assets including index-DUoo2CTB.js. No compile errors.

## Acceptance checked through rendered RTL/jsdom interactions

- Administrator creates a EUR client using form; approves a new marketer; uses actual checkbox assignment forms to assign original and new marketer to same client. Independent service inspection confirms both assignments.
- Assigned marketer fills all six metric fields for an unrecorded date, saves, reopens the same campaign/date, sees existing data, changes spend and saves. Exactly one record remains and version increments to 2.
- Client viewer has only its own client option and lacks entry/admin controls; reads report, filters to empty historical period and switches to Russian.
- Loading state appears while user request is pending; rejected authorization request renders the localized alert.
- Engineer interaction tests additionally exercise campaign creation, duplicate day editing, reversed date range and switching reporting currencies.

## Service invariants independently executed

Assigned/unassigned client isolation; client viewer mutation denial; admin-only user listing; immediate access and assignment revocation; unique campaign/date; stale versions rejected; inclusive date filters; archived metric writes rejected with retained report history; currency lock; valid dates/nonnegative and integer counts/two-decimal money; zero denominators; weighted ratios; no invented sales/leads inequality.

B01 regressions verify invalid merged role/client association rejects without changing original state, nonclient association is cleared, and former marketer assignments do not survive role transitions. Final 9/9 independent service tests passed.

## Limitations

No native browser, screenshots, live server preview, responsive rendering, contrast measurement or true browser E2E was executed. RTL renders real React components and exercises DOM interactions in jsdom. Real Google sign-in intentionally remains a later integration requirement; demo identities are explicitly mock preview. Google credentials, sessions, REST authorization, SQLite restart persistence and OpenAPI validation are outside this iteration and not claimed. No GitHub issue was created or closed. UI design remains subject to browser visual review when an approved browser capability is available.
