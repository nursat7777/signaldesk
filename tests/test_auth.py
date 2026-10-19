"""Auth tests inject a provider/session internally; production exposes no test login."""
from urllib.parse import parse_qs, urlparse
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core import MemoryRepository, Settings, now, token_hash
from backend.auth import COOKIE, STATE_COOKIE

@pytest.fixture
def setup():
    repo = MemoryRepository()
    settings = Settings(bootstrap_admin_email='admin@example.com')
    app = create_app(settings, repo)
    return app, repo, TestClient(app)

def test_public_status_and_no_production_bypass(setup):
    app, repo, client = setup
    assert client.get('/api/health').json() == {'status':'ok','storage':'memory'}
    assert client.get('/api/auth/status').json() == {'configured':False}
    assert client.get('/api/auth/google').status_code == 503
    assert client.get('/api/me').status_code == 401
    assert client.post('/api/test-login').status_code == 404
    assert len(repo.users) == 1
    assert next(iter(repo.users.values()))['googleSub'] is None

def login_fixture(repo, client):
    uid = next(iter(repo.users))
    token, csrf = repo.create_session(uid, 100)
    client.cookies.set(COOKIE, token)
    return uid, token, csrf

def test_session_csrf_logout_and_revocation(setup):
    app, repo, client = setup
    uid, token, csrf = login_fixture(repo,client)
    response = client.get('/api/me')
    assert response.status_code == 200 and response.headers['x-csrf-token'] == csrf
    assert 'googleSub' not in response.json()
    assert client.post('/api/auth/logout').status_code == 403
    assert client.post('/api/auth/logout',headers={'Origin':'https://evil.test','X-CSRF-Token':csrf}).status_code == 403
    assert client.post('/api/auth/logout',headers={'Origin':'http://localhost:5173','X-CSRF-Token':csrf}).status_code == 204
    assert token_hash(token) not in repo.sessions
    assert client.get('/api/me').status_code == 401
    login_fixture(repo, client)
    repo.users[uid]['enabled'] = False
    assert client.get('/api/me').status_code == 403

def test_expired_session(setup):
    app, repo, client = setup
    _, token, _ = login_fixture(repo,client)
    repo.sessions[token_hash(token)]['expires'] = now()-1
    assert client.get('/api/me').status_code == 401
    assert token_hash(token) not in repo.sessions

class FakeProvider:
    def authorization_url(self, settings, state, nonce):
        self.nonce=nonce
        return 'https://accounts.google.com/?state='+state
    async def identity(self, settings, code, nonce):
        assert nonce == self.nonce
        return {'email':'admin@example.com','sub':'verified-google-sub'}

def oauth_fixture():
    repo=MemoryRepository()
    app=create_app(Settings(google_client_id='client',google_client_secret='secret',bootstrap_admin_email='admin@example.com'),repo)
    app.state.oauth_provider=FakeProvider()
    return app,repo,TestClient(app)

def test_google_callback_browser_binding_rotation_replay():
    app,repo,client=oauth_fixture()
    old,_=repo.create_session(next(iter(repo.users)),100)
    client.cookies.set(COOKIE,old)
    start=client.get('/api/auth/google',follow_redirects=False)
    assert start.status_code==302 and 'HttpOnly' in start.headers['set-cookie']
    state=parse_qs(urlparse(start.headers['location']).query)['state'][0]
    other=TestClient(app)
    assert other.get('/api/auth/google/callback',params={'code':'code','state':state}).status_code==403
    result=client.get('/api/auth/google/callback',params={'code':'code','state':state},follow_redirects=False)
    assert result.status_code==302 and result.headers['location']=='http://localhost:5173'
    assert 'HttpOnly' in result.headers['set-cookie'] and 'SameSite=lax' in result.headers['set-cookie']
    assert token_hash(old) not in repo.sessions
    assert client.get('/api/me').status_code==200
    client.cookies.set(STATE_COOKIE,state,path='/api/auth/google/callback')
    assert client.get('/api/auth/google/callback',params={'code':'code','state':state}).status_code==403

@pytest.mark.parametrize('case',['unknown','disabled','mismatch','provider_error','expired','denied'])
def test_google_failures(case):
    app,repo,client=oauth_fixture()
    start=client.get('/api/auth/google',follow_redirects=False)
    state=parse_qs(urlparse(start.headers['location']).query)['state'][0]
    user=next(iter(repo.users.values()))
    if case=='unknown':user['email']='other@example.com'
    if case=='disabled':user['enabled']=False
    if case=='mismatch':user['googleSub']='different-sub'
    if case=='provider_error':
        async def fail(*args): raise ValueError('bad token')
        app.state.oauth_provider.identity=fail
    if case=='expired':repo.oauth_transactions[token_hash(state)]['expires']=now()-1
    params={'state':state,'code':'code'}
    if case=='denied':params={'state':state,'error':'access_denied'}
    result=client.get('/api/auth/google/callback',params=params)
    assert result.status_code==403 and set(result.json())=={'code','message'}
    assert not repo.sessions

def test_https_cookie_and_config_validation():
    settings=Settings(frontend_url='https://signaldesk.example')
    assert settings.secure_cookies
    with pytest.raises(ValueError):Settings(frontend_url='javascript:alert(1)')
