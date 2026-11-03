"""Real PostgreSQL checks. Run explicitly: TEST_DATABASE_URL=... .venv/bin/pytest integration -q

Requires a disposable database whose name includes 'test'. Each test creates and
finally removes its own isolated schema, never production application tables.
"""
import os
import uuid
from pathlib import Path
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core import Settings
from backend.database import make_engine, normalize_url
from backend.sql_repository import SQLRepository
from tests.support_seed import seed
from tests.test_sql_repository import test_shared_api_repository_behavior as shared_behavior
from tests.test_sql_repository import test_sql_concurrent_version_and_rollback as concurrency_check
from scripts.import_sqlite import import_sqlite

@pytest.fixture
def pg_url(monkeypatch):
    raw = os.environ['TEST_DATABASE_URL']
    parsed = make_url(normalize_url(raw))
    if parsed.get_backend_name() != 'postgresql' or 'test' not in (parsed.database or ''):
        raise ValueError('A disposable PostgreSQL database with test in its name is required')
    engine = make_engine(raw)
    schema = 'test_' + uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = parsed.update_query_dict({'options':f'-csearch_path={schema}'}).render_as_string(hide_password=False)
    monkeypatch.setenv('DATABASE_URL',url)
    try:
        command.upgrade(Config('alembic.ini'),'head')
        yield url
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()

def test_postgres_crud_money_constraints_and_versions(pg_url):
    shared_behavior(pg_url,'postgresql')

def test_postgres_concurrent_updates_and_rollback(pg_url):
    concurrency_check(pg_url)

def test_postgres_current_permissions_and_new_connection_persistence(pg_url):
    fixture = seed(pg_url)
    repo = SQLRepository(pg_url)
    app = create_app(Settings(database_url=pg_url),repo)
    with TestClient(app) as client:
        client.cookies.set('signaldesk_session', fixture['sessions']['client']['cookie'].split('=',1)[1])
        assert client.get('/api/me').status_code == 200
        assert client.get('/api/clients/fixture-other/campaigns').status_code == 403
        with repo.lock:
            repo.update('users','fixture-viewer',{'enabled':False})
        assert client.get('/api/me').status_code == 403
    repo.engine.dispose()
    reopened = SQLRepository(pg_url)
    with reopened.lock:
        assert reopened.get('users','fixture-viewer')['enabled'] is False
    reopened.engine.dispose()

def test_sqlite_import_preserves_values_and_refuses_nonempty(pg_url,tmp_path,monkeypatch):
    source = tmp_path/'legacy.sqlite3'
    sqlite_url = 'sqlite:///' + str(source)
    monkeypatch.setenv('DATABASE_URL',sqlite_url)
    command.upgrade(Config('alembic.ini'),'head')
    seed(sqlite_url)
    before = source.read_bytes()
    counts = import_sqlite(source,pg_url)
    assert counts['clients'] == 2 and counts['users'] == 3
    assert source.read_bytes() == before
    with pytest.raises(ValueError,match='not empty'):
        import_sqlite(source,pg_url)
    assert source.read_bytes() == before
    repo = SQLRepository(pg_url)
    with repo.engine.connect() as connection:
        assert connection.scalar(text('SELECT count(*) FROM sessions')) == 0
    repo.engine.dispose()
