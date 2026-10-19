# Iteration 3 — M08 engineer handoff

Implemented domain operations only; M09 report route and SQLite remain unimplemented.

- Strict closed request schemas with full metric input, fixed two-decimal string amounts, strict integer counts, nonempty patches, channel/currency/role enums.
- Administrator client/user/assignment management; normalized unique email; merged atomic role/client invariant; no self account edits; role transitions clear assignments.
- Assigned-client campaign creation/archive and daily metrics; read-only viewers; current permissions rechecked inside locked transactions; revoked access effective next request.
- Unique campaign/date, exact version updates and archive write guards, currency lock after any metric. Inclusive validated date ranges and Almaty future-entry rejection.
- Repository CRUD boundary returns defensive copies; lock spans check/write. Memory save_metric owns atomic create/version comparison. Later SQL implementation will use relational per-record transactions, not serialize memory state.
- Per-record numeric input caps: money <=999999999999.99 (12 integer digits), counts <=2147483647. These engineering precision limits preserve frontend cent arithmetic and safe ORM storage. Report totals remain unbounded aggregate strings/counts; PM coordinating explicit MoneyInput/CountInput contract schemas.

Engineer execution: `.venv/bin/python -m pytest -q` → 54 passed exit0 prior to independent M08 QA additions. Includes 13 new engineer domain cases, 41 existing auth/contract cases. Concurrency test simultaneously creates same campaign/day: one200, one409, exactly one row.

No commit, QA approval, external issue closure or Google live handshake claimed. Freeze pending independent QA; numeric-bound contract coordination remains explicit.
