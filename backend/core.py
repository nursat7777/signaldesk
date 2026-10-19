from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import os
import secrets
from threading import RLock
from urllib.parse import urlparse
from dotenv import load_dotenv


def now():
    return datetime.now(timezone.utc).timestamp()


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class Settings:
    google_client_id: str = ''
    google_client_secret: str = ''
    google_redirect_uri: str = 'http://localhost:8000/api/auth/google/callback'
    frontend_url: str = 'http://localhost:5173'
    allowed_origins: tuple = ('http://localhost:5173',)
    bootstrap_admin_email: str = ''
    session_seconds: int = 28800
    secure_cookies: bool = False

    def __post_init__(self):
        for url in (self.frontend_url, self.google_redirect_uri, *self.allowed_origins):
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                raise ValueError('Configured URLs must be absolute HTTP(S) URLs')
        if self.session_seconds <= 0:
            raise ValueError('Session lifetime must be positive')
        if self.frontend_url.startswith('https://'):
            self.secure_cookies = True

    @property
    def oauth_configured(self):
        return bool(self.google_client_id and self.google_client_secret)

    @classmethod
    def from_env(cls):
        load_dotenv()
        frontend = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return cls(google_client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
                   google_client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
                   google_redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback'),
                   frontend_url=frontend,
                   allowed_origins=tuple(x.strip() for x in os.getenv('ALLOWED_ORIGINS', frontend).split(',') if x.strip()),
                   bootstrap_admin_email=os.getenv('BOOTSTRAP_ADMIN_EMAIL', '').strip().lower(),
                   session_seconds=int(os.getenv('SESSION_SECONDS', '28800')))


@dataclass
class MemoryRepository:
    """Repository boundary; every compound mutation must hold lock."""
    storage: str = field(default='memory', init=False)
    users: dict = field(default_factory=dict)
    clients: dict = field(default_factory=dict)
    campaigns: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    sessions: dict = field(default_factory=dict)
    oauth_transactions: dict = field(default_factory=dict)
    lock: RLock = field(default_factory=RLock)

    def bootstrap(self, email):
        if not email:
            return
        with self.lock:
            if not any(u['email'] == email for u in self.users.values()):
                uid = secrets.token_urlsafe(16)
                self.users[uid] = dict(id=uid, email=email, name='Administrator', role='admin', enabled=True,
                                       clientId=None, clientIds=[], googleSub=None)

    def create_session(self, user_id, lifetime):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.sessions[token_hash(token)] = dict(userId=user_id, csrf=csrf, expires=now() + lifetime)
        return token, csrf


def public_user(user):
    return {k: user[k] for k in ('id', 'email', 'name', 'role', 'enabled', 'clientId', 'clientIds')}


class ApiError(Exception):
    def __init__(self, status, code, message=None):
        self.status, self.code, self.message = status, code, message or code
