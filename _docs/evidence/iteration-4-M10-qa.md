# M10 independent ORM schema/migration QA

Date2026-10-19. Independent reviewer. Local staged M10, no GitHub URL. Engineer frozen schema/migration only; application remains memory-backed until M11.

Verdict: PASS for M10 schema/migrations, not yet persistence gate.

Executed `.venv/bin/python -m pytest tests -q`: exit0,95 passed,4 known deprecation warnings. Seven independent tests/test_qa_migrations.py cases added to six engineer migration cases and previous regression suite.

Independent temporary databases run actual Alembic upgrade head twice; inspect all expected tables including version table. SQLAlchemy compare_metadata finds no schema/model drift. Both money columns are BIGINT integer minor units. ORM graph verifies campaign→client/metrics and user→assignment→client relationships, exact1025 minor units and timestamps.

Database-level FK rejects orphan campaign metric; check constraints reject negative money/count and zero version; unique campaign/date rejects duplicate without destroying original row; assignment composite key rejects duplicate; client role without associated client fails. Each failed transaction is rolled back and checked for unchanged persisted data. SQLite FK enforcement is enabled via engine connection event. Schema uses portable SQLAlchemy types/constraints; SQLite-specific setting is isolated to database engine adapter. No create_all shortcut replaces migration history.

Limits: this verifies actual relational schema and ORM writes on SQLite temporary files, not application repository persistence, process restart, cross-process optimistic writes or frontend integration. Those remain M11/M12. Browser/live Google/GitHub remain unverified. No external issue closure claimed.
