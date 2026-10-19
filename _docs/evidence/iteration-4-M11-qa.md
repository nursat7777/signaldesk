# M11 independent persistence QA — iteration4 gate

Date2026-10-19. Independent reviewer. Implementation commit67618a7. Local staged M11, no GitHub URL.

Verdict: PASS for persistent repository and full iteration4 gate; release frontend integration after checkpoint commit.

Executed `.venv/bin/python -m pytest tests -q`: exit0,122 passed,4 known deprecation warnings. Independent domain/report fixture is now parametrized for identical memory and migrated SQLite HTTP journeys. This reruns administrator setup, roles, assignments, revocation, validation, uniqueness/version edits, archives/currency lock and report/schema cases on SQL as well as memory. No ORM behavior accepted by inspection alone.

Additional independently authored tests/test_qa_sql_runtime.py:
- Two SQLRepository instances share one migrated file. First edits metric version1→2; second stale version1 update returns409. A deliberate exception after client update rolls back; subsequent independent repository read retains original client and exact20.25 metric/version2.
- Actual uvicorn factory subprocess launches against migrated file; health reports sqlite; existing fixture session authorizes /api/me; HTTP PUT changes metric to25.75/version2. Terminate process and wait for exit. Launch a second uvicorn process against same file; original persisted session still authenticates; real HTTP GET returns one metric25.75/version2 and report25.75/USD. Both server processes terminate at test end.

Independent targeted runtime run exit0,2passed, followed by complete122-test pass. Initial test harness failure inherited the environment SOCKS proxy for a loopback-only client; local test HTTP clients now use trust_env=False, without changing production provider networking. No application defect inferred. Earlier tests package import adjusted to tests.test_qa_domain after engineer added tests/__init__.py.

Source review: per-row SQLAlchemy repository, real relational tables, no JSON snapshots; request transaction commit/rollback, database unique key for simultaneous creates and conditional UPDATE with expected version for edits; persisted hashed sessions/OAuth transactions, default configured SQLite factory requires prior Alembic schema. No production fixture/login endpoint. Currency stored integer minor units and emitted exact strings.

Limitations: independent HTTP tests use internal test fixture identities and local server, not real Google consent or browser. Frontend still mock-backed until iteration5. Browser visual/real OAuth/deployment/GitHub remain unverified. PASS does not close or publish external issues.
