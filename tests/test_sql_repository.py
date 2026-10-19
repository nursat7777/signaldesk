from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import pytest
import httpx
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core import ApiError, MemoryRepository, Settings
from backend.sql_repository import SQLRepository
from tests.support_seed import seed

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def sql_url(tmp_path,monkeypatch):
    url='sqlite:///'+str(tmp_path/'persistent.sqlite3')
    monkeypatch.setenv('DATABASE_URL',url)
    command.upgrade(Config('alembic.ini'),'head')
    return url

@pytest.mark.parametrize('storage',['memory','sqlite'])
def test_shared_api_repository_behavior(sql_url,storage):
    repo=MemoryRepository() if storage=='memory' else SQLRepository(sql_url)
    app=create_app(Settings(database_url=sql_url,bootstrap_admin_email='admin@example.com'),repo)
    with repo.lock:uid=repo.all('users')[0]['id']
    token,csrf=repo.create_session(uid,3600)
    with TestClient(app) as client:
        client.cookies.set('signaldesk_session',token)
        client.headers.update({'Origin':'http://localhost:5173','X-CSRF-Token':csrf})
        assert client.get('/api/health').json()['storage']==storage
        cid=client.post('/api/clients',json={'name':'Coffee','currency':'KZT'}).json()['id']
        user=client.post('/api/users',json={'name':'Mark','email':'mark@example.com','role':'marketer','clientId':None}).json()
        assert client.put(f"/api/users/{user['id']}/assignments",json={'clientIds':[cid]}).status_code==204
        assert client.put(f"/api/users/{user['id']}/assignments",json={'clientIds':[cid]}).status_code==204
        campaign=client.post(f'/api/clients/{cid}/campaigns',json={'name':'Search','channel':'Google Ads'}).json()
        url=f"/api/campaigns/{campaign['id']}/metrics/2026-01-01"
        payload=dict(spend='0.10',revenue='0.30',impressions=0,clicks=5,leads=0,sales=7)
        assert client.put(url,json=payload).json()['version']==1
        assert client.put(url,json=payload).status_code==409
        assert client.put(url,json={**payload,'version':1,'spend':'0.20'}).json()['version']==2
        assert client.put(url,json={**payload,'version':1}).status_code==409
        report=client.get(f'/api/clients/{cid}/report',params={'from':'2026-01-01','to':'2026-01-01'}).json()
        assert report['totals']['spend']=='0.20' and report['totals']['ctr'] is None
        assert client.patch(f'/api/clients/{cid}',json={'currency':'EUR'}).status_code==409
        assert client.patch(f"/api/users/{user['id']}",json={'role':'client','clientId':'missing'}).status_code==422
        assert client.get('/api/users').json()[1 if storage=='memory' else next(i for i,u in enumerate(client.get('/api/users').json()) if u['id']==user['id'])]['role']=='marketer'
    if storage=='sqlite':repo.engine.dispose()


def test_sql_concurrent_version_and_rollback(sql_url):
    fixture=seed(sql_url)
    repo=SQLRepository(sql_url)
    with repo.lock:repo.insert('campaigns',dict(id='campaign',clientId='fixture-client',name='Search',channel='Other',archived=False))
    values=dict(spend='1.00',revenue='2.00',impressions=10,clicks=1,leads=1,sales=1)
    with repo.lock:repo.save_metric('campaign','2026-01-01',values,None)
    def update_once(_):
        other=SQLRepository(sql_url)
        try:
            with other.lock:other.save_metric('campaign','2026-01-01',values,1)
            return 200
        except ApiError as exc:return exc.status
        finally:other.engine.dispose()
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(update_once,range(2)))==[200,409]
    with pytest.raises(ApiError):
        with repo.lock:
            repo.update('clients','fixture-client',{'name':'Must roll back'})
            repo.insert('campaigns',dict(id='invalid',clientId='absent',name='Bad',channel='Other',archived=False))
    with repo.lock:
        assert repo.get('clients','fixture-client')['name']=='Fixture Coffee'
        assert repo.all('metrics')[0]['version']==2
    repo.engine.dispose()


def test_actual_uvicorn_restart_preserves_http_data_and_session(sql_url):
    fixture=seed(sql_url)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    environment={**os.environ,'DATABASE_URL':sql_url,'BOOTSTRAP_ADMIN_EMAIL':'admin@fixture.test'}
    def start():
        process=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app:create_app','--factory','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        for _ in range(100):
            if process.poll() is not None:raise AssertionError(process.stderr.read().decode())
            try:
                if httpx.get(f'http://127.0.0.1:{port}/api/health',timeout=.5,trust_env=False).status_code==200:return process
            except httpx.TransportError:pass
            time.sleep(.05)
        process.terminate();raise AssertionError('server did not start')
    headers={'Cookie':fixture['sessions']['admin']['cookie'],'Origin':fixture['origin'],'X-CSRF-Token':fixture['sessions']['admin']['csrf']}
    process=start()
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}',headers=headers,trust_env=False) as client:
            cid=client.post('/api/clients',json={'name':'Restart proof','currency':'EUR'}).json()['id']
            assert client.get('/api/me').status_code==200
    finally:process.terminate();process.wait(timeout=10)
    process=start()
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}',headers=headers,trust_env=False) as client:
            assert any(c['id']==cid and c['name']=='Restart proof' for c in client.get('/api/clients').json())
            assert client.get('/api/me').status_code==200
            assert client.get('/api/health').json()=={'status':'ok','storage':'sqlite'}
    finally:process.terminate();process.wait(timeout=10)


def test_missing_schema_clear_startup_failure(tmp_path):
    with pytest.raises(RuntimeError,match='alembic upgrade head'):
        SQLRepository('sqlite:///'+str(tmp_path/'missing.sqlite3'))
