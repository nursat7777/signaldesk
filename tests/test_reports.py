from pathlib import Path
import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from backend.app import create_app
from backend.core import MemoryRepository, Settings
from backend.auth import COOKIE
from backend.reporting import aggregate
from fastapi.testclient import TestClient


def test_exact_aggregate_sum_ratios_and_zero():
    rows=[dict(spend='0.10',revenue='0.20',impressions=1,clicks=1,leads=1,sales=1),dict(spend='0.20',revenue='0.40',impressions=99,clicks=2,leads=1,sales=2)]
    total=aggregate(rows)
    assert total['spend']=='0.30' and total['revenue']=='0.60'
    assert total['ctr']==3 and total['roas']==2
    assert total['cpc']==pytest.approx(.10) and total['cpl']==pytest.approx(.15)
    assert all(aggregate([])[k] is None for k in ('ctr','cpc','cpl','roas'))


def test_http_report_scope_dates_missing_days_and_schema():
    repo=MemoryRepository()
    app=create_app(Settings(bootstrap_admin_email='admin@example.com'),repo)
    client=TestClient(app)
    token,csrf=repo.create_session(next(iter(repo.users)),1000)
    client.cookies.set(COOKIE,token)
    client.headers.update({'Origin':'http://localhost:5173','X-CSRF-Token':csrf})
    cid=client.post('/api/clients',json={'name':'Coffee','currency':'KZT'}).json()['id']
    other=client.post('/api/clients',json={'name':'Studio','currency':'USD'}).json()['id']
    campaign=client.post(f'/api/clients/{cid}/campaigns',json={'name':'Search','channel':'Google Ads'}).json()['id']
    second=client.post(f'/api/clients/{cid}/campaigns',json={'name':'Social','channel':'Meta Ads'}).json()['id']
    third=client.post(f'/api/clients/{other}/campaigns',json={'name':'Other','channel':'Other'}).json()['id']
    base=dict(spend='0.10',revenue='0.30',impressions=10,clicks=2,leads=1,sales=1)
    for pid,day in ((campaign,'2026-01-01'),(second,'2026-01-03'),(third,'2026-01-02')):
        assert client.put(f'/api/campaigns/{pid}/metrics/{day}',json=base).status_code==200
    result=client.get(f'/api/clients/{cid}/report',params={'from':'2026-01-01','to':'2026-01-03'}).json()
    assert result['currency']=='KZT' and result['totals']['spend']=='0.20'
    assert [d['date'] for d in result['daily']]==['2026-01-01','2026-01-03']
    assert len(result['channels'])==2
    doc=yaml.safe_load((Path(__file__).resolve().parents[1]/'_docs/openapi.yml').read_text())
    Draft202012Validator({'$ref':'#/components/schemas/Report','components':doc['components']},format_checker=FormatChecker()).validate(result)
    assert client.get(f'/api/clients/{cid}/report',params={'from':'2026-02-01','to':'2026-01-01'}).status_code==422
    empty=client.get(f'/api/clients/{cid}/report',params={'from':'2025-01-01','to':'2025-01-01'}).json()
    assert empty['daily']==empty['channels']==[] and empty['totals']['roas'] is None
    viewer=client.post('/api/users',json={'name':'Viewer','email':'viewer@example.com','role':'client','clientId':cid}).json()
    token,_=repo.create_session(viewer['id'],1000)
    client.cookies.set(COOKIE,token)
    assert client.get(f'/api/clients/{other}/report',params={'from':'2026-01-01','to':'2026-01-03'}).status_code==403
    assert client.get(f'/api/clients/{cid}/report',params={'from':'2026-01-01','to':'2026-01-03'}).status_code==200


def test_all_maintained_operations_implemented_exactly():
    doc=yaml.safe_load((Path(__file__).resolve().parents[1]/'_docs/openapi.yml').read_text())
    expected={(path,method,op['operationId']) for path,item in doc['paths'].items() for method,op in item.items() if method in ('get','post','put','patch')}
    app=create_app(Settings(),MemoryRepository())
    actual={(path,method,op['operationId']) for path,item in app.openapi()['paths'].items() for method,op in item.items() if method in ('get','post','put','patch')}
    assert expected==actual
