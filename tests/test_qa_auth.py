"""Independent HTTP auth checks. Test-only repository sessions, never a login route."""
import pytest
from fastapi.testclient import TestClient
from urllib.parse import urlparse,parse_qs
from backend.app import create_app
from backend.core import Settings,MemoryRepository,token_hash,now
from backend.auth import COOKIE,STATE_COOKIE
@pytest.fixture
def authenv():
 repo=MemoryRepository();app=create_app(Settings(bootstrap_admin_email='admin@example.com'),repo);return app,repo,TestClient(app)
def install_session(repo,client):
 uid=next(iter(repo.users));token,csrf=repo.create_session(uid,60);client.cookies.set(COOKIE,token);return uid,token,csrf
def test_no_session_config_and_safe_identity(authenv):
 app,repo,c=authenv
 assert c.get('/api/health').json()=={'status':'ok','storage':'memory'}
 assert c.get('/api/me').status_code==401
 assert c.get('/api/auth/status').json()=={'configured':False}
 assert c.get('/api/auth/google',follow_redirects=False).status_code==503
 uid,token,csrf=install_session(repo,c);r=c.get('/api/me');assert r.status_code==200
 assert set(r.json())=={'id','email','name','role','enabled','clientId','clientIds'}
 assert r.headers['x-csrf-token']==csrf
 assert token not in repo.sessions and token_hash(token) in repo.sessions
 repo.users[uid]['enabled']=False;assert c.get('/api/me').status_code==403
@pytest.mark.parametrize('headers',[{}, {'Origin':'http://evil.example','X-CSRF-Token':'valid'}, {'Origin':'http://localhost:5173','X-CSRF-Token':'bad'}])
def test_logout_requires_origin_and_csrf(authenv,headers):
 app,repo,c=authenv;uid,token,csrf=install_session(repo,c)
 assert c.post('/api/auth/logout',headers=headers).status_code==403
 assert c.get('/api/me').status_code==200
 assert c.post('/api/auth/logout',headers={'Origin':'http://localhost:5173','X-CSRF-Token':csrf}).status_code==204
 assert c.get('/api/me').status_code==401
 assert token_hash(token) not in repo.sessions

def test_expired_session_and_unknown_cookie(authenv):
 app,repo,c=authenv;uid,token,csrf=install_session(repo,c);repo.sessions[token_hash(token)]['expires']=now()-1
 assert c.get('/api/me').status_code==401
 assert token_hash(token) not in repo.sessions
 c.cookies.set(COOKIE,'unknown');assert c.get('/api/me').status_code==401

class TestIdentityProvider:
 def authorization_url(self,settings,state,nonce):return f'https://accounts.example/authorize?state={state}&nonce={nonce}'
 async def identity(self,settings,code,nonce):
  assert code=='good' and nonce
  return {'email':'admin@example.com','sub':'verified-test-subject'}

def test_browser_bound_oauth_rotation_replay_and_secure_flags():
 settings=Settings(google_client_id='test-client',google_client_secret='test-secret',bootstrap_admin_email='admin@example.com',frontend_url='https://app.example',allowed_origins=('https://app.example',))
 repo=MemoryRepository();app=create_app(settings,repo);app.state.oauth_provider=TestIdentityProvider()
 c=TestClient(app,base_url='https://testserver');uid,old,csrf=install_session(repo,c)
 start=c.get('/api/auth/google',follow_redirects=False);assert start.status_code==302
 state=parse_qs(urlparse(start.headers['location']).query)['state'][0]
 assert all(x in start.headers['set-cookie'] for x in ['HttpOnly','SameSite=lax','Secure'])
 other=TestClient(app,base_url='https://testserver')
 assert other.get('/api/auth/google/callback',params={'state':state,'code':'good'},follow_redirects=False).status_code==403
 assert token_hash(state) in repo.oauth_transactions
 result=c.get('/api/auth/google/callback',params={'state':state,'code':'good'},follow_redirects=False)
 assert result.status_code==302 and result.headers['location']=='https://app.example'
 assert token_hash(old) not in repo.sessions
 assert c.get('/api/me').status_code==200
 assert repo.users[uid]['googleSub']=='verified-test-subject'
 assert token_hash(state) not in repo.oauth_transactions
 assert c.get('/api/auth/google/callback',params={'state':state,'code':'good'},follow_redirects=False).status_code==403

@pytest.mark.parametrize('invalid',['valid','nonce','audience','issuer','expired','unverified','signature'])
def test_real_provider_rejects_invalid_signed_claims(monkeypatch,invalid):
 """Exercise production JWT validation with signed local tokens; no Google network."""
 import asyncio
 from cryptography.hazmat.primitives.asymmetric import rsa
 from cryptography.hazmat.primitives import serialization
 from authlib.jose import JsonWebToken,JsonWebKey
 import backend.auth as module
 key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
 pem=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
 claims={'iss':'https://accounts.google.com','aud':'test-client','exp':int(now()+60),'sub':'subject','nonce':'nonce','email':'admin@example.com','email_verified':True}
 if invalid=='nonce':claims['nonce']='wrong'
 if invalid=='audience':claims['aud']='wrong'
 if invalid=='issuer':claims['iss']='https://attacker.example'
 if invalid=='expired':claims['exp']=int(now()-300)
 if invalid=='unverified':claims['email_verified']=False
 token=JsonWebToken(['RS256']).encode({'alg':'RS256'},claims,pem).decode()
 public=key.public_key()
 if invalid=='signature':public=rsa.generate_private_key(public_exponent=65537,key_size=2048).public_key()
 jwk=JsonWebKey.import_key(public.public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)).as_dict()
 class TokenClient:
  def __init__(self,*args,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def fetch_token(self,*args,**kwargs):return {'id_token':token}
 class CertClient(TokenClient):
  async def get(self,*args,**kwargs):
   import httpx
   return httpx.Response(200,json={'keys':[jwk]},request=httpx.Request('GET','https://example.test'))
 monkeypatch.setattr(module,'AsyncOAuth2Client',TokenClient)
 monkeypatch.setattr(module.httpx,'AsyncClient',CertClient)
 if invalid=='valid':
  assert asyncio.run(module.GoogleProvider().identity(Settings(google_client_id='test-client'),'code','nonce'))=={'email':'admin@example.com','sub':'subject'}
 else:
  with pytest.raises(Exception):asyncio.run(module.GoogleProvider().identity(Settings(google_client_id='test-client'),'code','nonce'))
