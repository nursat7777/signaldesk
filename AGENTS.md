# SignalDesk agent instructions

Approved scope is `_docs/plan.md`. Read `_docs/process.md`, architecture, design and testing guidelines before changing code. Follow the five iterations in order; frontend begins with mockService, then contract, in-memory backend, SQLite and integration. Do not build later iterations before earlier verification.

GitHub Issues are the canonical delivery backlog after publication. `_docs/backlog.json` is a local staging file, not proof that external issues exist. Every issue needs goal, description, acceptance criteria, out of scope and constraints. PM grooms one issue; engineer implements and commits while leaving it open; QA verifies criteria using executed checks and closes only after PASS. Genuine bugs need `user-test-bug` issues and regression evidence. Deferred `post-mvp` stays open.

Role instructions live in `_docs/team/`. The main orchestrator coordinates roles and keeps honest evidence; do not claim independent QA if the same implementation role performed the check. Record limitations explicitly. Never fabricate GitHub actions, transcripts, test results, OAuth completion or approvals. Do not store credentials in git. No production authentication bypass. Preserve SQLite migration history and the OpenAPI contract.
