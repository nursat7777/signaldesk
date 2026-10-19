# M13 — real HTTP / SQLite / React workflows

Date 2026-10-19. Released only after M12 independent PASS. No production application code changed during this task; test infrastructure and actual workflow verification added.

## Isolated environment

`frontend/test-support/server.ts` creates a temporary directory, runs real Alembic migrations against its SQLite file, then invokes `tests.support_seed` to provision approved accounts and isolated opaque sessions. It starts a real `uvicorn backend.app:create_app --factory` process on a free loopback port. Readiness follows server startup output, no fixed sleeps. Node HTTP transport supplies separate role cookie jars, trusted fixture Origin, and genuine adapter CSRF handling. Requests use actual network sockets; no mocked service/server endpoint. Stop sends SIGTERM, waits process exit and deletes only the temporary directory. Production code does not import helper/seeder and exposes no test login route. Session fixture setup does **not** verify live Google authentication.

## Executed checks

`npm test -- --run src/http-workflows.test.tsx`: **3/3 passed**, exit0, actual running server and SQLite. Journeys:

1. Administrator creates EUR client using form; approves a client-viewer account bound to it; assigns existing marketer to the newly created client; verifies actual backend results.
2. Marketer creates campaign, enters all six daily values with cents, reopens same day and edits revenue; one stored row remains with version2. Viewer sees exact money, no edit/admin controls, cross-client report access and attempted metric mutation reject. Date filter empty-state and RU switch work.
3. AuthGate logs out via backend; same session becomes401, honest unconfigured Google setup is shown, no demo identity fallback.

Initial engineer run exposed test timing errors, not application failures: stale DOM row click during previous save loading caused no assignment request; fixed by waiting for newly approved account render. Once assignment succeeded, client sorting selected the newly assigned client first; test now explicitly chooses intended fixture client. Actual assertions retained.

`npm run build`: TypeScript + Vite exit0 (269.42kB JavaScript/83.36kB gzip). Full suite result appended after completion. Independent QA adds distinct real HTTP scenarios using same infrastructure and owns final acceptance. No browser/visual QA claimed; RTL/jsdom does not prove actual browser layout or cookie policy behavior. OAuth credentials absent; real provider handshake remains unverified. No external repository actions/issue closures by this engineer.

Full run `npm test`: exit0, **35/35 across8files** including five actual HTTP workflow tests (engineer3, independent QA2). QA additionally observed an immediate query racing post-save reload on another execution; changed that test to await account action readiness before clicking. Production application unchanged. Final independent QA rerun verifies this last harness refinement.
