"""CLI-only isolated fixtures; never copied into the production image."""
import json
import os
import uuid
from backend.core import Settings
from backend.app import create_app
from backend.sql_repository import SQLRepository


def seed():
    url = os.environ['E2E_TEST_DATABASE_URL']
    if 'test' not in url.split('?', 1)[0].rsplit('/', 1)[-1]:
        raise ValueError('Fixture database name must contain test')
    key = uuid.uuid4().hex[:12]
    repo = SQLRepository(url)
    create_app(Settings(database_url=url), repo)
    with repo.lock:
        for suffix, currency in [('client', 'KZT'), ('other', 'USD')]:
            repo.insert('clients', dict(id=f'{key}-{suffix}', name=f'{key} {suffix}', currency=currency, archived=False))
        for role in ['admin', 'marketer', 'client']:
            repo.insert('users', dict(id=f'{key}-{role}', email=f'{key}-{role}@fixture.test', name=f'{key} {role}', role=role, enabled=True, clientId=f'{key}-client' if role=='client' else None, clientIds=[f'{key}-client'] if role=='marketer' else [], googleSub=None))
        repo.insert('campaigns', dict(id=f'{key}-campaign', clientId=f'{key}-client', name=f'{key} Search', channel='Google Ads', archived=False))
    sessions = {}
    for role in ['admin', 'marketer', 'client']:
        token, csrf = repo.create_session(f'{key}-{role}', 3600)
        sessions[role] = dict(token=token, csrf=csrf)
    repo.engine.dispose()
    return dict(key=key, clientId=f'{key}-client', otherId=f'{key}-other', campaignId=f'{key}-campaign', sessions=sessions)

if __name__ == '__main__':
    print(json.dumps(seed()))
