"""Independent report sums and maintained-contract runtime response checks."""
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator,FormatChecker
from test_qa_domain import domainenv,BASE,DAY
from backend.app import create_app
from backend.core import Settings,MemoryRepository
DOC=yaml.safe_load((Path(__file__).resolve().parents[1]/'_docs/openapi.yml').read_text())
def check(name,value):Draft202012Validator({'$ref':f'#/components/schemas/{name}','components':DOC['components']},format_checker=FormatChecker()).validate(value)
def test_weighted_report_missing_dates_and_schema(domainenv):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv
 assert c.put(f"/api/campaigns/{p['id']}/metrics/2026-01-02",json=BASE,headers=h).status_code==200
 assert c.put(f"/api/campaigns/{p['id']}/metrics/2026-01-04",json={'spend':'89.75','revenue':'264.25','impressions':900,'clicks':50,'leads':5,'sales':3},headers=h).status_code==200
 r=c.get(f"/api/clients/{c1['id']}/report",params={'from':'2026-01-01','to':'2026-01-05'});assert r.status_code==200
 report=r.json();check('Report',report)
 assert report['currency']=='USD' and report['totals']==dict(spend='100.00',revenue='300.00',impressions=1000,clicks=100,leads=10,sales=5,ctr=10,cpc=1,cpl=10,roas=3)
 assert [d['date'] for d in report['daily']]==['2026-01-02','2026-01-04']
 assert len(report['channels'])==1 and report['channels'][0]['channel']=='Google Ads'
 assert report['channels'][0]['totals']==report['totals']
 assert c.patch(f"/api/campaigns/{p['id']}",json={'archived':True},headers=h).status_code==200
 assert c.get(f"/api/clients/{c1['id']}/report",params={'from':'2026-01-01','to':'2026-01-05'}).json()['totals']==report['totals']

def test_empty_zero_and_scope_report(domainenv):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv
 q={'from':'2026-01-01','to':'2026-01-05'};empty=c.get(f"/api/clients/{c1['id']}/report",params=q).json();check('Report',empty)
 assert empty['daily']==[] and empty['channels']==[]
 assert all(empty['totals'][k] is None for k in ['ctr','cpc','cpl','roas'])
 zero={**BASE,'spend':'0.00','revenue':'0.00','impressions':0,'clicks':0,'leads':0,'sales':0}
 assert c.put(f"/api/campaigns/{p['id']}/metrics/{DAY}",json=zero,headers=h).status_code==200
 report=c.get(f"/api/clients/{c1['id']}/report",params=q).json();assert len(report['daily'])==1
 assert all(report['totals'][k] is None for k in ['ctr','cpc','cpl','roas'])
 as_user(v['id']);assert c.get(f"/api/clients/{c2['id']}/report",params=q).status_code==403
 assert c.get(f"/api/clients/{c1['id']}/report",params={'from':'2026-02-30','to':'2026-03-02'}).status_code==422
 assert c.get(f"/api/clients/{c1['id']}/report",params={'from':'2026-01-05','to':'2026-01-01'}).status_code==422
 c.cookies.clear();assert c.get(f"/api/clients/{c1['id']}/report",params=q).status_code==401

def test_runtime_api_routes_match_maintained_contract():
 app=create_app(Settings(),MemoryRepository())
 actual={(m,p) for p,v in app.openapi()['paths'].items() for m in v if m in {'get','post','put','patch','delete'}}
 expected={(m,p) for p,v in DOC['paths'].items() for m in v if m in {'get','post','put','patch','delete'}}
 assert actual==expected

def test_domain_success_responses_match_maintained_schema(domainenv):
 repo,c,as_user,admin,h,c1,c2,m,v,p=domainenv
 for obj in [c1,c2]:check('Client',obj)
 for obj in [m,v,c.get('/api/me').json()]:check('User',obj)
 check('Campaign',p)
 row=c.put(f"/api/campaigns/{p['id']}/metrics/{DAY}",json=BASE,headers=h);check('Metric',row.json())
 for path in ['/api/clients','/api/users',f"/api/clients/{c1['id']}/campaigns"]:assert c.get(path).status_code==200
