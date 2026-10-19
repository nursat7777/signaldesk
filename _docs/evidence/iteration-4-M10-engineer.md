# Iteration 4 — M10 engineer handoff

Created relational SQLAlchemy schema and genuine Alembic revision0001. Application still runs memory repository; persistent repository M11 not implemented.

Tables: clients, users with nullable Google subject and client association, composite-key marketer assignments, campaigns, unique campaign/date daily_metrics, hashed sessions and one-time OAuth transactions. Foreign keys and ORM relationships connect entities; checks enforce valid role/client association, enums and nonnegative counts/cents/version. Money BigInteger minor units, calendar date DATE, UTC timestamps. No JSON state columns, no runtime create_all.

Migration command: `DATABASE_URL=sqlite:////absolute/path/file.sqlite3 .venv/bin/python -m alembic upgrade head`. Default path from alembic.ini is local signaldesk.sqlite3. Schema upgrade only, no automatic demo users. SQLite FK pragma enabled for every ORM/migration connection. All database files excluded from git.

Engineer command `.venv/bin/python -m pytest tests/test_migrations.py -q` →6passed exit0: fresh and repeat upgrade, relationship traversal, session links, uniqueness, foreign keys, count/money/role constraints and rollback. Full regression executed separately before QA handoff.

Ready/frozen for independent M10 QA; no stage4 runtime switch or restart-persistence claim yet. No commits or issue closures claimed.
