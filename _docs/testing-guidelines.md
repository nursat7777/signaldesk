# Testing guidelines

Run tests and record exact command, environment, result and limitations. Compilation is not interaction testing. Do not claim Google authentication was tested end-to-end without actual configured Google credentials and a successful real sign-in.

## Required checks

- Unit: aggregate ratios from base totals, denominator zero, integer/decimal validation, Almaty date boundaries, currency invariants and stale version logic.
- Frontend interactions against mockService: role navigation, client selection, date filters, daily create/edit/duplicate flow, RU/EN, loading/empty/error states and keyboard form use.
- Contract: parse OpenAPI, validate it with a real validator, compare routes and request/response semantics. FastAPI's generated schema alone is not verification of a maintained contract.
- In-memory API: admin, assigned/unassigned marketer and client viewer, 401/403 paths, archived data, invalid metrics, duplicates, optimistic conflicts, revoked users/assignments and report aggregation.
- SQLite: fresh migrations, ORM relations/unique constraints, repository behavior parity, transaction rollback and data read after a real backend process restart using the same file.
- Integrated E2E: administrator manages client and access; marketer creates campaign and daily metrics; client viewer sees correct own report and cannot modify or access another client; reload persistence; languages and responsive screen states.
- Regression: rerun relevant case after every fix and full suite at completion.

## Evidence format

Date/stage/issue URL; commit; command or interaction; expected and actual result; exit status/count; log/screenshot path; reviewer; PASS/FAIL; limitations. No fabricated screenshots, issue URLs or test counts. Distinguish isolated dependency-overridden auth tests from real Google login.

## Bug lifecycle

Create issue with `user-test-bug`, exact reproduction, expected/actual behavior and impact. PM grooms; QA defines regression scenario; engineer fixes; QA reruns scenario and affected journeys. Close only after PASS. Independent QA must state its evidence; orchestrator self-checks are labeled self-checks.

## Current environment limitations

The required browser-control skill is unavailable in this managed container. Do not launch a browser preview, install a browser or improvise a browser fallback. Use actual frontend interaction tests through React Testing Library/jsdom and real-server HTTP end-to-end workflow checks. Explicitly report that browser/visual QA is not verified. Real Google OAuth credentials are absent; provider callback tests may mock the provider under clearly labeled isolated tests, but the live Google handshake remains unverified.

## Current assignment override — 2026-11-03

The user's new assignment explicitly requires Playwright. Pinned Chromium was
installed and 17 scenarios executed against actual static frontend/FastAPI with
SQLite compatibility storage; this replaces the old browser-unavailable restriction
for this phase. PostgreSQL and Docker Compose must still pass actual CI checks.
Provider authentication remains distinct from CLI-seeded server session tests.
New evidence is orchestrator self-check evidence, not independent QA approval.
