"""CI-only restart probe; state contains a temporary test token and is never uploaded."""
import json
import os
import sys
import time
from pathlib import Path
import httpx
from scripts.e2e_seed import seed

path = Path('.restart-test-state.json')
base = os.environ.get('E2E_BASE_URL','http://localhost:8000')
if sys.argv[1] == 'prepare':
    data = seed()
    path.write_text(json.dumps(data))
    path.chmod(0o600)
else:
    data = json.loads(path.read_text())
    try:
        with httpx.Client(base_url=base,trust_env=False,cookies={'signaldesk_session':data['sessions']['admin']['token']}) as client:
            for _ in range(30):
                try:
                    if client.get('/api/health').status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(1)
            assert client.get('/api/me').status_code == 200
            assert any(c['id']==data['clientId'] for c in client.get('/api/clients').json())
        print('Restart preserved the database record and server session')
    finally:
        path.unlink(missing_ok=True)
