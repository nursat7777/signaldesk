import json
import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from backend.app import create_app
from backend.core import Settings, MemoryRepository
from backend.telemetry import Telemetry


@pytest.fixture(autouse=True)
def isolated_telemetry(monkeypatch):
    monkeypatch.setenv('OTEL_TRACES_SAMPLER', 'always_on')
    monkeypatch.setenv('STATIC_DIR', '/nonexistent-signaldesk-unit-static')


def setup():
    reader, exporter = InMemoryMetricReader(), InMemorySpanExporter()
    telemetry = Telemetry(reader=reader, span_processor=SimpleSpanProcessor(exporter))
    repo = MemoryRepository()
    app = create_app(Settings(bootstrap_admin_email='admin@example.test'), repo, telemetry)
    user = repo.all('users')[0]
    token, csrf = repo.create_session(user['id'], 3600)
    client = TestClient(app)
    client.cookies.set('signaldesk_session', token)
    return client, telemetry, reader, exporter, {'X-CSRF-Token': csrf, 'Origin': 'http://localhost:5173'}


def points(reader):
    return {m.name: m.data.data_points for r in reader.get_metrics_data().resource_metrics for s in r.scope_metrics for m in s.metrics}


def test_bounded_routes_propagation_and_private_data(capsys):
    client, t, reader, exporter, headers = setup()
    secret = 'DO_NOT_EXPORT_SECRET'
    response = client.get('/api/me?token='+secret, headers={'traceparent': '00-'+'1'*32+'-'+'2'*16+'-01', 'Authorization': secret})
    assert response.status_code == 200
    client.get('/api/private-'+secret)
    spans = exporter.get_finished_spans()
    assert spans[0].context.trace_id == int('1'*32, 16)
    assert spans[0].parent.span_id == int('2'*16, 16)
    assert secret not in str([(s.name, dict(s.attributes)) for s in spans])
    p = points(reader)
    assert sum(x.value for x in p['signaldesk_http_requests']) == 2
    assert {x.attributes['http.route'] for x in p['signaldesk_http_requests']} == {'/api/me', 'unmatched'}
    logs = capsys.readouterr().err
    assert secret not in logs
    assert json.loads(logs.splitlines()[0])['trace_id'] == '1'*32
    t.shutdown()


def test_real_business_success_validation_and_permissions():
    client, t, reader, exporter, headers = setup()
    response = client.post('/api/clients', json={'name': 'Client', 'currency': 'USD'}, headers=headers)
    assert response.status_code == 201
    cid = response.json()['id']
    campaign = client.post('/api/clients/'+cid+'/campaigns', json={'name': 'Campaign', 'channel': 'Other'}, headers=headers)
    assert campaign.status_code == 201
    pid = campaign.json()['id']
    metric = {'spend': '1.00', 'revenue': '2.00', 'impressions': 10, 'clicks': 3, 'leads': 1, 'sales': 1}
    assert client.put('/api/campaigns/'+pid+'/metrics/2020-01-01', json=metric, headers=headers).status_code == 200
    assert client.get('/api/clients/'+cid+'/report?from=2020-01-01&to=2020-01-01').status_code == 200
    assert client.post('/api/users', json={'name': 'Reader', 'email': 'reader@example.test', 'role': 'client', 'clientId': cid}, headers=headers).status_code == 201
    assert client.post('/api/clients', json={'name': '', 'currency': 'bad'}, headers=headers).status_code == 422
    p = points(reader)
    for op in ('client_create', 'campaign_create', 'daily_metric_save', 'report_generate', 'user_create'):
        assert any(x.attributes['outcome'] == 'success' and x.value == 1 for x in p['signaldesk_'+op])
    assert sum(x.value for x in p['signaldesk_business_failures']) == 1
    user = next(u for u in client.app.state.repo.all('users') if u['role'] == 'client')
    token, csrf = client.app.state.repo.create_session(user['id'], 3600)
    client.cookies.set('signaldesk_session', token)
    assert client.post('/api/clients', json={'name': 'Forbidden', 'currency': 'USD'}, headers={**headers, 'X-CSRF-Token': csrf}).status_code == 403
    assert sum(x.value for x in points(reader)['signaldesk_permission_denials']) == 1
    t.shutdown()


def test_database_child_spans_omit_sql_parameters(tmp_path):
    from sqlalchemy import create_engine, text
    reader, exporter = InMemoryMetricReader(), InMemorySpanExporter()
    t = Telemetry(reader=reader, span_processor=SimpleSpanProcessor(exporter))
    engine = create_engine('sqlite:///'+str(tmp_path/'trace.db'))
    t.instrument_database(engine)
    with t.tracer.start_as_current_span('request') as parent:
        with engine.connect() as connection:
            assert connection.execute(text('SELECT :secret'), {'secret': 'PRIVATE_VALUE'}).scalar() == 'PRIVATE_VALUE'
            try:
                connection.execute(text('SELECT * FROM absent_table'))
            except Exception:
                pass
    spans = exporter.get_finished_spans()
    db = [s for s in spans if s.name == 'database SELECT']
    assert len(db) == 2
    assert all(s.parent.span_id == parent.get_span_context().span_id for s in db)
    assert any(s.status.status_code.name == 'ERROR' for s in db)
    assert 'PRIVATE_VALUE' not in str([(s.name, dict(s.attributes), s.events) for s in spans])
    engine.dispose()
    t.shutdown()


def test_otel_log_export_correlates_and_redacts():
    from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
    exporter = InMemoryLogRecordExporter()
    t = Telemetry(log_processor=SimpleLogRecordProcessor(exporter))
    client = TestClient(create_app(Settings(), MemoryRepository(), t))
    assert client.get('/api/auth/status?secret=PRIVATE_QUERY').status_code == 200
    record = exporter.get_finished_logs()[0].log_record
    body = json.loads(record.body)
    assert body['trace_id'] == format(record.trace_id, '032x')
    assert body['span_id'] == format(record.span_id, '016x')
    assert body['route'] == '/api/auth/status'
    assert 'PRIVATE_QUERY' not in str((record.body, dict(record.attributes)))
    t.shutdown()
