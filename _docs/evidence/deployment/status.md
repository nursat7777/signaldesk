# Deployment-phase self-verification — 2026-11-03

Baseline from upstream a51cd59 archive: 124 Python and 35 frontend tests passed.
After PostgreSQL adapter/static serving and mobile accessible labels:
- `.venv/bin/pytest -q`: 126 passed (regression-python-2.log copied as python.log).
- `npm test -- --maxWorkers=1` in frontend: see frontend.log.
- `npm run build` in frontend: TypeScript/Vite passed.
- `npm run e2e`: 17 passed, Chromium Playwright 1.56.1, 28 seconds; static frontend
  + real API + disposable SQLite. Not a PostgreSQL or Docker pass.
- `.venv/bin/ruff check --select E9,F63,F7,F82 backend scripts tests integration`: pass.
- `.venv/bin/cfn-lint infra/cloudformation.yaml`: pass.

Initial browser run: 12 passed/5 failed. Three failures were test harness mistakes
(missing required metric date query, duplicate alert locator); fixed without
changing assertions about application outcomes. Two genuine defects were tracked
before fixes: #46 mobile icon buttons lost names; #47 SPA wildcard changed unknown
POST API from 404 to 405. Final full browser and Python regression passed.

PostgreSQL binaries were downloaded, but initdb could not switch from mapped root
(setpriv: setresuid failed: Invalid argument). Docker was absent and extracted
binary lacked runtime dependencies. No actual PostgreSQL/image/Compose success is
claimed. CI defines mandatory real Compose/PostgreSQL gates. No tests were skipped
or deleted to achieve the executed counts. Integration suite execution pending.

CloudFormation local static lint is not AWS API validation or a deployed stack.
No Render/AWS account access, credit verification or production OAuth configuration
was provided. No billing/resource operations performed. GitHub Actions execution
and remote publication results are recorded only after actual observation.
