# Iteration 4 — M11 engineer handoff

SQLRepository now performs relational per-record reads/writes within thread-local units of work. Role/client checks and writes share transaction boundaries. Daily writes use database campaign/date uniqueness for creates and conditional SQL UPDATE against expected version for updates, so separate repository instances cannot silently overwrite. Failed constraints roll back all prior changes within the transaction. Session digests, Google subjects and atomic one-time OAuth transactions persist in relational tables.

Production is a factory: `python -m uvicorn backend.app:create_app --factory`. No eager default application at import; explicit MemoryRepository remains available for historical tests. Omitted repository selects SQLRepository using DATABASE_URL. Missing migration fails with actionable startup error; no create_all or automatic seed. Run `make migrate`, then `make backend`.

Engineer test command `.venv/bin/python -m pytest tests/test_sql_repository.py -q` →5passed exit0. Includes shared memory/SQL HTTP behavior, same-assignment replacement, CAS across distinct repository instances, transaction rollback, missing-schema failure and actual uvicorn subprocess restart with same file and session token proving data and authorization persist. First subprocess check hit environment SOCKS proxy setup when local httpx trusted proxy env; isolated loopback client changed to trust_env=False and rerun passed. No production network/proxy settings changed.

Test-only fixture command: migrate temp database, then `DATABASE_URL=... python -m tests.support_seed` prints roles/session cookies/CSRF/client IDs. Production never imports test module or exposes identity injection routes. Stage5 frontend may use actual HTTP with this isolated fixture; it does not constitute live Google login evidence.

Ready/frozen for independent M11 QA. No stage5 frontend edits, QA approval, commits or external issue closure claimed. Live Google handshake unverified.
