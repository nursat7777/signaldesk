"""Independent persistent HTTP process restart and cross-repository CAS tests."""
import os,socket,subprocess,sys,time
from datetime import date
import pytest,httpx
from alembic import command
from alembic.config import Config
from backend.sql_repository import SQLRepository
from backend.core import ApiError
VALUES=dict(spend='10.25',revenue='35.75',impressions=100,clicks=50,leads=5,sales=2)
@pytest.fixture
def sql_seed(tmp_path,monkeypatch):
 url='sqlite:///'+str(tmp_path/'qa-process.sqlite3');monkeypatch.setenv('DATABASE_URL',url);command.upgrade(Config('alembic.ini'),'head');r=SQLRepository(url);r.bootstrap('qa-admin@example.com')
 with r.lock:
  uid=r.all('users')[0]['id'];r.insert('clients',dict(id='c1',name='QA persisted',currency='USD',archived=False));r.insert('campaigns',dict(id='p1',clientId='c1',name='QA persistent campaign',channel='Google Ads',archived=False));r.save_metric('p1','2026-01-02',VALUES,None)
 token,csrf=r.create_session(uid,3600)
 yield url,r,token,csrf,tmp_path
 r.engine.dispose()
def test_two_repository_stale_edit_and_transaction_rollback(sql_seed):
 url,r,token,csrf,tmp=sql_seed;other=SQLRepository(url)
 try:
  with r.lock:r.save_metric('p1','2026-01-02',{**VALUES,'spend':'20.25'},1)
  with pytest.raises(ApiError) as conflict:
   with other.lock:other.save_metric('p1','2026-01-02',VALUES,1)
  assert conflict.value.status==409
  with pytest.raises(RuntimeError):
   with other.lock:
    other.update('clients','c1',{'name':'Must rollback'});raise RuntimeError('test rollback')
  with r.lock:
   assert r.get('clients','c1')['name']=='QA persisted'
   row=r.all('metrics')[0];assert row['spend']=='20.25' and row['version']==2
 finally:other.engine.dispose()
def test_actual_server_process_restart_preserves_data_session_and_report(sql_seed):
 url,r,token,csrf,tmp=sql_seed
 sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();base=f'http://127.0.0.1:{port}'
 env={**os.environ,'DATABASE_URL':url,'BOOTSTRAP_ADMIN_EMAIL':'qa-admin@example.com'}
 def start(log):
  proc=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app:create_app','--factory','--host','127.0.0.1','--port',str(port)],env=env,stdout=log,stderr=log)
  for _ in range(100):
   if proc.poll() is not None:raise AssertionError('Backend exited before health readiness')
   try:
    if httpx.get(base+'/api/health',timeout=.3,trust_env=False).status_code==200:return proc
   except httpx.HTTPError:pass
   time.sleep(.05)
  proc.terminate();proc.wait(timeout=5);raise AssertionError('Backend did not become ready')
 with open(tmp/'qa-server.log','wb') as log:
  proc=start(log)
  try:
   with httpx.Client(base_url=base,cookies={'signaldesk_session':token},trust_env=False) as c:
    assert c.get('/api/health').json()['storage']=='sqlite'
    assert c.get('/api/me').status_code==200
    updated=c.put('/api/campaigns/p1/metrics/2026-01-02',json={**VALUES,'spend':'25.75','version':1},headers={'Origin':'http://localhost:5173','X-CSRF-Token':csrf});assert updated.status_code==200
  finally:proc.terminate();proc.wait(timeout=10)
  proc=start(log)
  try:
   with httpx.Client(base_url=base,cookies={'signaldesk_session':token},trust_env=False) as c:
    assert c.get('/api/me').status_code==200
    rows=c.get('/api/clients/c1/metrics',params={'from':'2026-01-02','to':'2026-01-02'}).json();assert len(rows)==1 and rows[0]['spend']=='25.75' and rows[0]['version']==2
    report=c.get('/api/clients/c1/report',params={'from':'2026-01-02','to':'2026-01-02'}).json();assert report['totals']['spend']=='25.75' and report['currency']=='USD'
  finally:proc.terminate();proc.wait(timeout=10)
