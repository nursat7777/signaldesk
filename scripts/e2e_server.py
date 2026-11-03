"""Start only a disposable local test database and the actual production app."""
import os
import sys
from pathlib import Path
from alembic import command
from alembic.config import Config

path = Path('.e2e-test.sqlite3').resolve()
os.environ['DATABASE_URL'] = 'sqlite:///' + str(path)
os.environ['FRONTEND_URL'] = 'http://127.0.0.1:8000'
os.environ['ALLOWED_ORIGINS'] = 'http://127.0.0.1:8000'
command.upgrade(Config('alembic.ini'), 'head')
os.execv(sys.executable, [sys.executable, '-m', 'uvicorn', 'backend.app:create_app', '--factory', '--host', '127.0.0.1', '--port', '8000'])
