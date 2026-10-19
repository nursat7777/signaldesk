"""Independent contract acceptance checks; run before any backend exists."""
from pathlib import Path
import re
import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate_spec
DOC=yaml.safe_load((Path(__file__).resolve().parents[1]/'_docs/openapi.yml').read_text())
SCHEMAS=DOC['components']['schemas']
def validator(name):
 return Draft202012Validator({'$ref':f'#/components/schemas/{name}','components':DOC['components']},format_checker=FormatChecker())
def test_openapi_structure_and_unique_operations():
 validate_spec(DOC)
 ops=[v for path in DOC['paths'].values() for k,v in path.items() if k in {'get','post','put','patch','delete'}]
 assert len(ops)==19
 ids=[x['operationId'] for x in ops]
 assert len(set(ids))==len(ids)
 assert {'getMe','listClients','createClient','updateClient','listCampaigns','createCampaign','updateCampaign','listMetrics','saveMetric','listUsers','createUser','updateUser','setAssignments'}<=set(ids)
def test_auth_mutation_and_error_contract():
 public={'/api/health','/api/auth/status','/api/auth/google','/api/auth/google/callback'}
 for path,item in DOC['paths'].items():
  for method,op in item.items():
   if method not in {'get','post','put','patch'}:continue
   assert op['security']==([] if path in public else [{'sessionCookie':[]}])
   assert {'401','403','404','409','422','503'}<=set(op['responses'])
   if method!='get':
    headers={p['name'] for p in op.get('parameters',[]) if p['in']=='header' and p['required']}
    assert {'Origin','X-CSRF-Token'}<=headers
@pytest.mark.parametrize('name,value', [('Money','0.00'),('Money','10.25'),('MetricWrite',{'spend':'0.00','revenue':'10.25','impressions':0,'clicks':5,'leads':0,'sales':1}),('UserCreate',{'name':'Ada','email':'ada@example.com','role':'client','clientId':'c1'}),('Assignments',{'clientIds':['c1','c2']})])
def test_valid_schema_examples(name,value):validator(name).validate(value)
@pytest.mark.parametrize('name,value',[('Money',10.25),('Money','-1.00'),('Money','1.001'),('Money','01.00'),('MetricWrite',{'spend':'0.00','revenue':'0.00','impressions':-1,'clicks':0,'leads':0,'sales':0}),('MetricWrite',{'spend':'0.00','revenue':'0.00','impressions':0,'clicks':1.1,'leads':0,'sales':0}),('UserCreate',{'name':'  ','email':'ada@example.com','role':'admin','clientId':None}),('UserPatch',{}),('Assignments',{'clientIds':['c1','c1']})])
def test_invalid_schema_examples(name,value):assert list(validator(name).iter_errors(value))
def test_empty_report_example():
 totals=dict(spend='0.00',revenue='0.00',impressions=0,clicks=0,leads=0,sales=0,ctr=None,cpc=None,cpl=None,roas=None)
 validator('Report').validate(dict(clientId='c1',currency='KZT',**{'from':'2026-10-01','to':'2026-10-19'},totals=totals,daily=[],channels=[]))

@pytest.mark.parametrize('value,valid',[('999999999999.99',True),('1000000000000.00',False)])
def test_input_money_bound(value,valid):assert (not list(validator('MoneyInput').iter_errors(value))) is valid
@pytest.mark.parametrize('value,valid',[(2147483647,True),(2147483648,False)])
def test_input_count_bound(value,valid):assert (not list(validator('CountInput').iter_errors(value))) is valid

def test_output_aggregate_not_limited_to_input_bounds():
 validator('Money').validate('1000000000000.00')
 totals=dict(spend='1000000000000.00',revenue='0.00',impressions=2147483648,clicks=0,leads=0,sales=0,ctr=0,cpc=None,cpl=None,roas=0)
 validator('Totals').validate(totals)
