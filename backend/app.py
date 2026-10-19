import secrets
from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException
from .auth import COOKIE, STATE_COOKIE, GoogleProvider, current_session, mutation_session
from .core import ApiError, MemoryRepository, Settings, now, public_user, token_hash


def create_app(settings=None, repository=None):
    settings = settings or Settings.from_env()
    if repository is None:
        from .sql_repository import SQLRepository
        repository = SQLRepository(settings.database_url)
    repo = repository
    repo.bootstrap(settings.bootstrap_admin_email)
    app = FastAPI(title='SignalDesk', version='1.0.0')
    app.state.repo, app.state.settings, app.state.oauth_provider = repo, settings, GoogleProvider()
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=True,
                       allow_methods=['GET', 'POST', 'PUT', 'PATCH'],
                       allow_headers=['Content-Type', 'X-CSRF-Token'], expose_headers=['X-CSRF-Token'])

    @app.exception_handler(ApiError)
    async def api_error(request, exc):
        return JSONResponse({'code': exc.code, 'message': exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = exc.errors()
        locations = {part for error in errors for part in error['loc']}
        missing = any(error['type'] == 'missing' for error in errors)
        code = 'required' if missing else 'invalidEmail' if 'email' in locations else 'invalidNumber' if locations & {'spend', 'revenue', 'impressions', 'clicks', 'leads', 'sales', 'version'} else 'required'
        return JSONResponse({'code': code, 'message': 'Invalid request fields'}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse({'code': 'notFound' if exc.status_code == 404 else 'required',
                             'message': str(exc.detail)}, status_code=exc.status_code)

    @app.get('/api/health', operation_id='health')
    def health():
        return {'status': 'ok', 'storage': repo.storage}

    @app.get('/api/auth/status', operation_id='authStatus')
    def auth_status():
        return {'configured': settings.oauth_configured}

    @app.get('/api/me', operation_id='getMe')
    def me(response: Response, auth=Depends(current_session)):
        user, session = auth
        response.headers['X-CSRF-Token'] = session['csrf']
        return public_user(user)

    @app.post('/api/auth/logout', status_code=204, operation_id='logout')
    def logout(request: Request, auth=Depends(mutation_session)):
        with repo.lock:
            repo.session_delete(token_hash(request.cookies.get(COOKIE, '')))
        response = Response(status_code=204)
        response.delete_cookie(COOKIE, httponly=True, secure=settings.secure_cookies, samesite='lax')
        return response

    @app.get('/api/auth/google', operation_id='startGoogleLogin')
    def google_start():
        if not settings.oauth_configured:
            raise ApiError(503, 'oauthNotConfigured', 'Configure Google OAuth credentials and approved administrator email')
        state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with repo.lock:
            repo.oauth_begin(token_hash(state), nonce, now() + 600)
        response = RedirectResponse(app.state.oauth_provider.authorization_url(settings, state, nonce), status_code=302)
        response.set_cookie(STATE_COOKIE, state, max_age=600, httponly=True, secure=settings.secure_cookies,
                            samesite='lax', path='/api/auth/google/callback')
        return response

    @app.get('/api/auth/google/callback', operation_id='googleCallback')
    async def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
        if not settings.oauth_configured:
            raise ApiError(503, 'oauthNotConfigured')
        browser_state = request.cookies.get(STATE_COOKIE, '')
        # Never consume another browser's transaction on a mismatched cookie.
        if not state or not secrets.compare_digest(state, browser_state):
            raise ApiError(403, 'oauthFailed', 'Invalid browser-bound OAuth state')
        with repo.lock:
            transaction = repo.oauth_consume(token_hash(state))
        if not transaction or transaction['expires'] <= now() or not code or error:
            raise ApiError(403, 'oauthFailed', 'Expired or invalid OAuth transaction')
        try:
            identity = await app.state.oauth_provider.identity(settings, code, transaction['nonce'])
        except ApiError:
            raise
        except Exception:
            raise ApiError(403, 'oauthFailed', 'Google identity verification failed')
        with repo.lock:
            user = next((u for u in repo.all('users') if u['email'] == identity['email']), None)
            if not user or not user['enabled'] or (user['googleSub'] and user['googleSub'] != identity['sub']):
                raise ApiError(403, 'forbidden')
            repo.update('users', user['id'], {'googleSub': identity['sub']})
            repo.session_delete(token_hash(request.cookies.get(COOKIE, '')))
            token, _ = repo.create_session(user['id'], settings.session_seconds)
        response = RedirectResponse(settings.frontend_url, status_code=302)
        response.delete_cookie(STATE_COOKIE, path='/api/auth/google/callback')
        response.set_cookie(COOKIE, token, max_age=settings.session_seconds, httponly=True,
                            secure=settings.secure_cookies, samesite='lax')
        return response
    from .domain import router
    app.include_router(router())
    from .reporting import router as report_router
    app.include_router(report_router())
    return app

