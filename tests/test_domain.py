from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core import MemoryRepository, Settings
from backend.auth import COOKIE

@pytest.fixture
def env():
    repo=MemoryRepository()
    app=create_app(Settings(bootstrap_admin_email='admin@example.com'),repo)
    admin=next(iter(repo.users))
    def session(uid):
        client=TestClient(app)
        token,csrf=repo.create_session(uid,3600)
        client.cookies.set(COOKIE,token)
        client.headers.update({'Origin':'http://localhost:5173','X-CSRF-Token':csrf})
        return client
    return repo,app,session,session(admin)

def create(env):
    repo,app,session,admin=env
    client=admin.post('/api/clients',json={'name':'Coffee','currency':'KZT'}).json()
    other=admin.post('/api/clients',json={'name':'Studio','currency':'USD'}).json()
    marketer=admin.post('/api/users',json={'name':'Marketer','email':'MARK@example.com','role':'marketer','clientId':'ignored'}).json()
    viewer=admin.post('/api/users',json={'name':'Viewer','email':'viewer@example.com','role':'client','clientId':client['id']}).json()
    assert admin.put(f"/api/users/{marketer['id']}/assignments",json={'clientIds':[client['id']]}).status_code==204
    return client,other,marketer,viewer

def payload():return {'spend':'10.25','revenue':'45.30','impressions':0,'clicks':5,'leads':0,'sales':7}

def test_role_scope_admin_assignment_revocation(env):
    repo,app,session,admin=env
    client,other,marketer,viewer=create(env)
    mark=session(marketer['id']); view=session(viewer['id'])
    assert mark.get('/api/clients').json()==[client]
    assert view.get('/api/clients').json()==[client]
    for actor in (mark,view):
        assert actor.get(f"/api/clients/{other['id']}/campaigns").status_code==403
        assert actor.post('/api/clients',json={'name':'x','currency':'EUR'}).status_code==403
        assert actor.get('/api/users').status_code==403
    assert view.post(f"/api/clients/{client['id']}/campaigns",json={'name':'Search','channel':'Google Ads'}).status_code==403
    campaign=mark.post(f"/api/clients/{client['id']}/campaigns",json={'name':'Search','channel':'Google Ads'}).json()
    assert campaign['clientId']==client['id']
    assert admin.put(f"/api/users/{marketer['id']}/assignments",json={'clientIds':[]}).status_code==204
    assert mark.patch(f"/api/campaigns/{campaign['id']}",json={'name':'Other'}).status_code==403
    assert admin.patch(f"/api/users/{viewer['id']}",json={'enabled':False}).status_code==200
    assert view.get('/api/clients').status_code==403

def test_daily_uniqueness_version_currency_archive(env):
    repo,app,session,admin=env
    client,other,marketer,viewer=create(env)
    campaign=admin.post(f"/api/clients/{client['id']}/campaigns",json={'name':'Search','channel':'Google Ads'}).json()
    url=f"/api/campaigns/{campaign['id']}/metrics/2026-01-01"
    metric=admin.put(url,json=payload()).json()
    assert metric['version']==1 and metric['spend']=='10.25'
    assert admin.put(url,json=payload()).status_code==409
    updated=admin.put(url,json={**payload(),'version':1,'spend':'15.00'})
    assert updated.status_code==200 and updated.json()['version']==2
    assert admin.put(url,json={**payload(),'version':1}).status_code==409
    assert admin.put(url+'2',json=payload()).status_code==422
    assert admin.patch(f"/api/clients/{client['id']}",json={'currency':'USD'}).status_code==409
    assert admin.patch(f"/api/clients/{client['id']}",json={'archived':True}).status_code==200
    assert admin.put(url,json={**payload(),'version':2}).status_code==409
    assert admin.patch(f"/api/campaigns/{campaign['id']}",json={'archived':True}).status_code==409
    rows=admin.get(f"/api/clients/{client['id']}/metrics",params={'from':'2026-01-01','to':'2026-01-01'}).json()
    assert len(rows)==1 and rows[0]['spend']=='15.00'

@pytest.mark.parametrize('patch',[{'clicks':1.5},{'clicks':True},{'spend':10.25},{'spend':'01.00'},{'spend':'1.001'},{'sales':-1},{'spend':'92233720368547758.08'},{'version':None},{'extra':0}])
def test_metric_strict_validation(env,patch):
    repo,app,session,admin=env
    client,_,_,_=create(env)
    campaign=admin.post(f"/api/clients/{client['id']}/campaigns",json={'name':'Search','channel':'Other'}).json()
    assert admin.put(f"/api/campaigns/{campaign['id']}/metrics/2026-01-01",json={**payload(),**patch}).status_code==422
    assert not repo.metrics

def test_user_patch_invariant_atomic_and_self_guard(env):
    repo,app,session,admin=env
    client,_,marketer,viewer=create(env)
    url=f"/api/users/{marketer['id']}"
    assert admin.patch(url,json={'role':'client','clientId':'missing','enabled':False}).status_code==422
    unchanged=repo.get('users',marketer['id'])
    assert unchanged['role']=='marketer' and unchanged['enabled'] and unchanged['clientIds']==[client['id']]
    changed=admin.patch(url,json={'role':'client','clientId':client['id']}).json()
    assert changed['clientIds']==[]
    changed=admin.patch(url,json={'role':'marketer'}).json()
    assert changed['clientId'] is None and changed['clientIds']==[]
    assert admin.patch(f"/api/users/{next(iter(repo.users))}",json={'enabled':False}).status_code==409
    assert admin.post('/api/users',json={'name':'Duplicate','email':'MARK@example.com','role':'admin','clientId':None}).status_code==409

def test_dates_ranges_and_concurrent_unique_create(env):
    repo,app,session,admin=env
    client,_,_,_=create(env)
    campaign=admin.post(f"/api/clients/{client['id']}/campaigns",json={'name':'Search','channel':'Other'}).json()
    for day in ('2026-02-30','20260101','2099-01-01'):
        assert admin.put(f"/api/campaigns/{campaign['id']}/metrics/{day}",json=payload()).status_code==422
    assert admin.get(f"/api/clients/{client['id']}/metrics",params={'from':'2026-02-01','to':'2026-01-01'}).status_code==422
    url=f"/api/campaigns/{campaign['id']}/metrics/2026-01-01"
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(lambda _:admin.put(url,json=payload()).status_code,range(2)))
    assert sorted(statuses)==[200,409] and len(repo.metrics)==1
