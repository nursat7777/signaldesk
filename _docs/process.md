# Delivery process

## Approval and source provenance

The user approved the presented specification on 2026-10-19: “да давай сделать и не забудь зайти в мой гит”. The proposed completion details in plan.md are now accepted engineering scope. SignalDesk is an implementation working name, not a fabricated brainstorming answer.

Methodology sources: https://aishippingblog.com/p/ai-native-development-specifications and https://aishippingblog.com/p/build-and-ship-a-full-stack-app-with. Source-reading claims and quotations require actual retrieved evidence; this document defines the assignment's explicit required process.

## Role handoff

1. PM selects one issue, checks prerequisites, fills the template and records grooming.
2. Engineer implements only that issue and runs relevant checks, commits changes, and leaves the issue open.
3. QA independently inspects acceptance criteria, executes tests and actual interactions, and records commands, results and limitations.
4. Only PASS permits closure. FAIL produces reproduction details; genuine discovered bugs receive `user-test-bug` and pass through PM → QA test case → engineer fix → regression → QA closure.

The main orchestrator coordinates role handoffs. Automated test execution alone is not independent QA approval. Do not claim external publication, closure, identity verification or deployment without observed evidence.

## Required iterations and gates

| Iteration | Deliverable | Evidence required before the next iteration |
|---|---|---|
| 1 | React frontend using centralized mockService | Principal role journeys, metric editing, duplicate-date behavior, filters and RU/EN interactions run against mocks |
| 2 | `_docs/openapi.yml` derived from service needs | Parse/validate schemas, endpoint coverage, auth/error semantics review |
| 3 | FastAPI with in-memory repository | Actual API tests for validation, permissions, calculations, uniqueness and stale updates |
| 4 | SQLAlchemy/Alembic/SQLite repository | Migration execution, shared repository behavior tests and real process restart persistence |
| 5 | Frontend real API client | Running integrated journeys, role isolation, regression suite and maintained contract |

Record a checkpoint commit/evidence for each stage; do not retroactively pretend all-at-once development was iterative.

## GitHub

Create labels `mvp`, `post-mvp`, `user-test-bug`. `_docs/backlog.json` is unpublished staging until actual issue URLs are recorded. Publish meaningful issues in dependency order; keep post-MVP deferred. All required markdown goes into git. Completion requires all MVP and discovered user-test-bug issues closed after QA PASS and every implemented change pushed.

## Evidence register

Stage 0 documentation received local independent QA evidence at `_docs/evidence/iteration-0-qa.md` (implementation commit `4a06645`). Stage 1 received local independent QA PASS at `_docs/evidence/iteration-1-qa.md`, with 16 frontend tests and build evidence (implementation commit `156c8de`, tag `iteration-1-mock-verified`). B01 was reproduced, groomed, fixed and verified locally; `_docs/bugs.json` preserves evidence. GitHub publication remains pending; no external issue closures exist. Browser/visual QA and real Google handshake remain unverified. See `_docs/evidence/methodology-limitations.md` for bundled issue sequencing and external flow deviations. Stage 2 contract engineer validation is recorded separately; implementation stages require independent release gates.
