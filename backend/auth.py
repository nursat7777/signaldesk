"""Real Google Authorization Code/OpenID Connect integration, no simulated login route."""
import secrets
from urllib.parse import urlencode
import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import JsonWebToken
from fastapi import Depends, Request
from .core import ApiError, now, token_hash

COOKIE = 'signaldesk_session'
STATE_COOKIE = 'signaldesk_oauth_state'


class GoogleProvider:
    def authorization_url(self, settings, state, nonce):
        return 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(dict(
            client_id=settings.google_client_id, redirect_uri=settings.google_redirect_uri,
            response_type='code', scope='openid email profile', state=state, nonce=nonce))

    async def identity(self, settings, code, nonce):
        async with AsyncOAuth2Client(settings.google_client_id, settings.google_client_secret) as client:
            token = await client.fetch_token('https://oauth2.googleapis.com/token', code=code,
                                             redirect_uri=settings.google_redirect_uri)
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get('https://www.googleapis.com/oauth2/v3/certs')
            response.raise_for_status()
            jwks = response.json()
        claims = JsonWebToken(['RS256']).decode(token['id_token'], jwks, claims_options={
            'iss': {'essential': True, 'values': ['https://accounts.google.com', 'accounts.google.com']},
            'aud': {'essential': True, 'value': settings.google_client_id},
            'exp': {'essential': True}, 'sub': {'essential': True},
            'nonce': {'essential': True, 'value': nonce}})
        claims.validate(leeway=30)
        if claims.get('email_verified') is not True or not claims.get('email'):
            raise ApiError(403, 'forbidden', 'Google email must be verified')
        return dict(email=claims['email'].strip().lower(), sub=claims['sub'])


def current_session(request: Request):
    repo = request.app.state.repo
    token = request.cookies.get(COOKIE, '')
    with repo.lock:
        session = repo.session_get(token_hash(token))
        if not session or session['expires'] <= now():
            if session:
                repo.session_delete(token_hash(token))
            raise ApiError(401, 'unauthorized')
        user = repo.get('users', session['userId'])
        if not user or not user['enabled']:
            raise ApiError(403, 'forbidden')
        return user, session


def mutation_session(request: Request, auth=Depends(current_session)):
    user, session = auth
    origin = request.headers.get('origin')
    csrf = request.headers.get('x-csrf-token', '')
    if origin not in request.app.state.settings.allowed_origins or not secrets.compare_digest(csrf, session['csrf']):
        raise ApiError(403, 'csrf')
    return user, session


def require_admin(user):
    if user['role'] != 'admin' or not user['enabled']:
        raise ApiError(403, 'forbidden')
