from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core import MemoryRepository, Settings


def test_production_frontend_and_api_routes(tmp_path, monkeypatch):
    (tmp_path / 'assets').mkdir()
    (tmp_path / 'index.html').write_text('<html>SignalDesk build</html>')
    (tmp_path / 'assets/app.js').write_text('console.log("app")')
    monkeypatch.setenv('STATIC_DIR', str(tmp_path))
    client = TestClient(create_app(Settings(), MemoryRepository()))
    assert 'SignalDesk build' in client.get('/').text
    assert 'SignalDesk build' in client.get('/dashboard').text
    assert client.get('/assets/app.js').headers['content-type'].startswith('text/javascript')
    assert client.get('/api/health').json()['status'] == 'ok'
    assert client.get('/api/unknown').status_code == 404
    assert client.get('/api/me').status_code == 401
    assert client.get('/assets/missing.js').status_code == 404
