# Methodology and verification limitations

## External GitHub workflow

The user authorized GitHub setup and implementation. GitHub tooling/connection was unavailable before development began. `_docs/backlog.json` therefore stages planned issues locally with `pending_publish` status; these are not actual GitHub Issues. No external open times, comments, labels, closures, QA approvals or issue URLs may be inferred from local staging. If connection becomes available, publish honestly at the actual time and link existing work; do not backdate history. Consequently the assignment's exact external issue-first flow has not been fully followed.

## Issue sequencing deviation

M01 documentation was groomed locally. Frontend iteration work covers M02–M05 together, rather than implementing and independently verifying exactly one groomed issue at a time. This is a real process deviation, not evidence that four separate issue handoffs happened. Preserve the stage checkpoint and map each criterion to files/tests. From this checkpoint onward select one dependency-ready local/published issue, record PM handoff, engineer changes and independent QA evidence before moving on. Do not retrospectively label bundled work as isolated issue implementation.

## Initial traceability review

This review maps artifacts present when written; it is not acceptance approval. Paths may grow as implementation proceeds.

| Issue | Existing artifacts | Acceptance status |
|---|---|---|
| M01 | AGENTS.md, CLAUDE.md, README.md, _docs/plan.md, process.md, architecture.md, design-system.md, testing-guidelines.md, task-template.md, team/*.md, both transcripts | Documentation prepared; external commit/push/QA evidence belongs in delivery record |
| M02 | frontend/src/service.ts; frontend/src/qa.service.test.ts | Central mock interface and role fixtures exist; no rendered navigation or language acceptance established by this review |
| M03 | frontend/src/service.ts | Client/user/assignment operations exist; UI interactions and role-edit invariants require independent QA |
| M04 | frontend/src/service.ts | Daily uniqueness, version and validation logic exist; running interaction/edge-case verification pending |
| M05 | frontend/src/service.ts aggregate/listMetrics | Ratio calculation/filter primitives exist; reporting UI and all required states pending verification |
| M06–M14 | No artifacts assessed in this review | Not verified |
| P01–P02 | Local backlog proposals only | Deferred |

## Acceptance consistency findings for QA

- Architecture prescribes fixed decimal strings at API boundaries; current mock Metric uses numbers. Iteration 2 must explicitly map the typed UI model to exact API decimal amounts or revise the documented representation with rationale. Avoid silent contract mismatch.
- The mock Service interface computes reports client-side from authorized metric lists. A report endpoint is an architectural proposal, not a frontend service operation already present. Iteration 2 must agree actual adapter operations before generating the contract.
- Mock user update currently permits role/clientId combinations without the same invariant used at creation. QA should exercise changing an approved user to client without a valid client association and role changes that retain prior assignment state. Findings are candidates until reproduced, not already verified bug claims.
- Available tests can establish programmatic behavior. Browser-control tooling and live Google credentials are unavailable, so browser/visual QA and real provider handshake remain unverified.

## Bug grooming

Initial review had no bug file. Subsequently QA reproduced B01 with an actual failing Vitest run and staged `_docs/bugs.json`; PM groomed the observed finding locally. No GitHub publication or QA PASS is implied. When QA records a reproduced finding, PM must add goal, reproduction, expected/actual, acceptance criteria, scope, constraints and dependencies before engineer fix. Local bugs must retain `pending_publish` while external GitHub remains unavailable.
