"""Test-only fixture command: migrate temp DB separately, then print opaque test sessions.

DATABASE_URL=sqlite:////tmp/test.sqlite3 python -m tests.support_seed
Never exposed by HTTP; production application does not import this module.
"""
import json
import os
from backend.core import Settings
from backend.app import create_app
from backend.sql_repository import SQLRepository


def seed(url):
    repo=SQLRepository(url)
    settings=Settings(database_url=url,bootstrap_admin_email='admin@fixture.test')
    app=create_app(settings,repo)
    with repo.lock:
        admin=next(u for u in repo.all('users') if u['email']=='admin@fixture.test')
        for data in [dict(id='fixture-client',name='Fixture Coffee',currency='KZT',archived=False),dict(id='fixture-other',name='Fixture Studio',currency='USD',archived=False)]:
            if not repo.get('clients',data['id']):repo.insert('clients',data)
        for data in [dict(id='fixture-marketer',name='Fixture Marketer',email='marketer@fixture.test',role='marketer',clientId=None,clientIds=['fixture-client']),
                     dict(id='fixture-viewer',name='Fixture Viewer',email='viewer@fixture.test',role='client',clientId='fixture-client',clientIds=[])]:
            if not repo.get('users',data['id']):repo.insert('users',{**data,'enabled':True,'googleSub':None})
    sessions={}
    for role,uid in [('admin',admin['id']),('marketer','fixture-marketer'),('client','fixture-viewer')]:
        token,csrf=repo.create_session(uid,3600)
        sessions[role]={'cookie':'signaldesk_session='+token,'csrf':csrf,'userId':uid}
    repo.engine.dispose()
    return {'sessions':sessions,'clientId':'fixture-client','otherClientId':'fixture-other','origin':'http://localhost:5173'}

if __name__=='__main__':
    print(json.dumps(seed(os.environ['DATABASE_URL'])))
