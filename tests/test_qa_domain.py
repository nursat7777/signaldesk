"""Independent domain HTTP acceptance against repository injected into production app."""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core import Settings,MemoryRepository
from backend.auth import COOKIE
DAY='2026-01-02'
BASE={'spend':'10.25','revenue':'35.75','impressions':100,'clicks':50,'leads':5,'sales':2}
@pytest.fixture
def domainenv():
 repo=MemoryRepository();app=create_app(Settings(bootstrap_admin_email='admin@example.com'),repo);c=TestClient(app)
 def as_user(uid):
  c.cookies.clear();token,csrf=repo.create_session(uid,3600);c.cookies.set(COOKIE,token);return {'Origin':'http://localhost:5173','X-CSRF-Token':csrf}
 admin=next(iter(repo.users));headers=as_user(admin)
 def post(path,data):
  r=c.post(path,json=data,headers=headers);assert r.status_code==201,r.text;return r.json()
 c1=post('/api/clients',{'name':'QA One','currency':'USD'})
 c2=post('/api/clients',{'name':'QA Two','currency':'EUR'})
 marketer=post('/api/users',{'name':'QA Marketer','email':'QA@EXAMPLE.COM','role':'marketer','clientId':None})
 viewer=post('/api/users',{'name':'QA Viewer','email':'viewer@example.com','role':'client','clientId':c1['id']})
 assert c.put(f"/api/users/{marketer['id']}/assignments",json={'clientIds':[c1['id']]},headers=headers).status_code==204
 campaign=post(f"/api/clients/{c1['id']}/campaigns",{'name':'QA Search','channel':'Google Ads'})
 return repo,c,as_user,admin,headers,c1,c2,marketer,viewer,campaign

def test_role_id_boundaries_and_revocation(domainenv):
 repo,c,as_user,admin,h,c1,c2,marketer,viewer,p=domainenv
 mh=as_user(marketer['id']);assert [x['id'] for x in c.get('/api/clients').json()]==[c1['id']]
 assert c.get(f"/api/clients/{c2['id']}/campaigns").status_code==403
 assert c.get('/api/users').status_code==403
 assert c.post('/api/clients',json={'name':'No','currency':'USD'},headers=mh).status_code==403
 vh=as_user(viewer['id']);assert c.put(f"/api/campaigns/{p['id']}/metrics/{DAY}",json=BASE,headers=vh).status_code==403
 assert c.patch(f"/api/campaigns/{p['id']}",json={'archived':True},headers=vh).status_code==403
 h=as_user(admin);assert c.put(f"/api/users/{marketer['id']}/assignments",json={'clientIds':[]},headers=h).status_code==204
 as_user(marketer['id']);assert c.get(f"/api/clients/{c1['id']}/campaigns").status_code==403
 h=as_user(admin);assert c.patch(f"/api/users/{viewer['id']}",json={'enabled':False},headers=h).status_code==200
 as_user(viewer['id']);assert c.get('/api/clients').status_code==403

def test_unique_stale_archive_currency_exactness(domainenv):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv;path=f"/api/campaigns/{p['id']}/metrics/{DAY}"
 created=c.put(path,json=BASE,headers=h);assert created.status_code==200;assert created.json()['spend']=='10.25'
 assert c.put(path,json=BASE,headers=h).status_code==409
 changed=c.put(path,json={**BASE,'spend':'0.00','version':1},headers=h);assert changed.status_code==200 and changed.json()['version']==2
 assert c.put(path,json={**BASE,'version':1},headers=h).status_code==409
 rows=c.get(f"/api/clients/{c1['id']}/metrics",params={'from':DAY,'to':DAY}).json();assert len(rows)==1 and rows[0]['spend']=='0.00'
 assert c.patch(f"/api/clients/{c1['id']}",json={'currency':'KZT'},headers=h).status_code==409
 assert c.patch(f"/api/clients/{c1['id']}",json={'archived':True},headers=h).status_code==200
 assert c.put(path,json={**BASE,'version':2},headers=h).status_code==409
 assert c.patch(f"/api/campaigns/{p['id']}",json={'name':'No'},headers=h).status_code==409
 assert len(c.get(f"/api/clients/{c1['id']}/metrics",params={'from':DAY,'to':DAY}).json())==1

@pytest.mark.parametrize('patch',[{'clicks':1.5},{'clicks':True},{'clicks':-1},{'spend':10.25},{'spend':'1.001'},{'spend':'-1.00'},{'revenue':'92233720368547758.08'},{'impressions':9223372036854775808},{'version':None}])
def test_invalid_metric_wire_values(domainenv,patch):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv
 r=c.put(f"/api/campaigns/{p['id']}/metrics/{DAY}",json={**BASE,**patch},headers=h)
 assert r.status_code==422 and set(r.json())=={'code','message'}

@pytest.mark.parametrize('day',['2026-02-30','20260102','2999-01-01'])
def test_invalid_calendar_days(domainenv,day):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv
 assert c.put(f"/api/campaigns/{p['id']}/metrics/{day}",json=BASE,headers=h).status_code==422

def test_account_merged_validation_and_no_stale_grants(domainenv):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv
 assert m['email']=='qa@example.com'
 assert c.patch(f"/api/users/{m['id']}",json={'role':'client'},headers=h).status_code==422
 row=c.patch(f"/api/users/{m['id']}",json={'role':'client','clientId':c1['id']},headers=h).json();assert row['clientIds']==[]
 row=c.patch(f"/api/users/{m['id']}",json={'role':'marketer'},headers=h).json();assert row['clientId'] is None and row['clientIds']==[]
 assert c.patch(f"/api/users/{v['id']}",json={'clientId':'missing'},headers=h).status_code==422
 row=next(x for x in c.get('/api/users').json() if x['id']==v['id']);assert row['clientId']==c1['id']
 assert c.patch(f'/api/users/{admin}',json={'enabled':False},headers=h).status_code==409

def test_documented_input_numeric_boundaries(domainenv):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv;path=f"/api/campaigns/{p['id']}/metrics/{DAY}"
 r=c.put(path,json={**BASE,'spend':'999999999999.99','impressions':2147483647},headers=h);assert r.status_code==200
 assert r.json()['spend']=='999999999999.99' and r.json()['impressions']==2147483647
 for patch in [{'spend':'1000000000000.00'},{'clicks':2147483648}]:assert c.put(path,json={**BASE,**patch,'version':1},headers=h).status_code==422
