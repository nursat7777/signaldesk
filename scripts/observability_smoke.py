"""Actual stack checks; run inside app container on the private telemetry network."""
import json
import os
import hashlib
import base64
from datetime import datetime, timedelta, timezone
import time
import urllib.parse
import urllib.request


def get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read()


def main():
    endpoints = ['http://collector:13133/', 'http://prometheus:9090/-/ready', 'http://alertmanager:9093/-/ready', 'http://tempo:3200/ready', 'http://loki:3100/ready', 'http://grafana:3000/api/health', 'http://incident-agent:8080/health']
    for endpoint in endpoints:
        for attempt in range(45):
            try:
                get(endpoint)
                break
            except Exception:
                if attempt == 44:
                    raise
                time.sleep(2)
    # Cause a real request and wait for OTLP export + scrape + log/trace indexing.
    trace_id = '1234567890abcdef1234567890abcdef'
    request = urllib.request.Request('http://app:8000/api/health', headers={'traceparent': '00-'+trace_id+'-1234567890abcdef-01'})
    with urllib.request.urlopen(request, timeout=5) as response:
        assert json.load(response)['storage'] == 'postgresql'
    for attempt in range(45):
        try:
            query = urllib.parse.urlencode({'query': 'signaldesk_http_requests_total'})
            data = json.loads(get('http://prometheus:9090/api/v1/query?'+query))
            assert data['data']['result'], 'No application metrics'
            pg = json.loads(get('http://prometheus:9090/api/v1/query?query=pg_up'))
            assert any(float(r['value'][1]) == 1 for r in pg['data']['result']), 'Database exporter unavailable'
            assert get('http://tempo:3200/api/traces/'+trace_id), 'Missing correlated trace'
            if os.getenv('APP_ENV') == 'test':
                for operation in ('client_create', 'campaign_create', 'daily_metric_save', 'report_generate', 'user_create'):
                    query = urllib.parse.urlencode({'query': 'sum(signaldesk_'+operation+'_total{outcome="success"})'})
                    result = json.loads(get('http://prometheus:9090/api/v1/query?'+query))['data']['result']
                    assert result and float(result[0]['value'][1]) > 0, 'Missing real business metric: '+operation
                auth = base64.b64encode(('admin:'+os.environ['GRAFANA_ADMIN_PASSWORD']).encode()).decode()
                request = urllib.request.Request('http://grafana:3000/api/dashboards/uid/signaldesk-operations', headers={'Authorization': 'Basic '+auth})
                with urllib.request.urlopen(request, timeout=5) as response:
                    dashboard = json.load(response)['dashboard']
                assert len(dashboard['panels']) >= 15, 'Grafana dashboard provisioning failed'

            log_query = urllib.parse.urlencode({'query': '{service_name="signaldesk"}', 'limit': 10})
            logs = json.loads(get('http://loki:3100/loki/api/v1/query_range?'+log_query))
            assert logs['data']['result'], 'No structured application logs'
            break
        except Exception:
            if attempt == 44:
                raise
            time.sleep(2)
    if os.getenv('APP_ENV') == 'test':
        # Disposable CI only. Exercise actual Alertmanager -> authenticated responder.
        token = os.environ['ALERT_WEBHOOK_TOKEN']
        key = hashlib.sha256(b'test:HighErrorRate').hexdigest()
        start = datetime.now(timezone.utc)-timedelta(minutes=1)
        def send_alert(end):
            payload = [{'labels': {'alertname': 'HighErrorRate', 'deployment_environment_name': 'test', 'severity': 'warning'}, 'startsAt': start.isoformat(), 'endsAt': end.isoformat()}]
            request = urllib.request.Request('http://alertmanager:9093/api/v2/alerts', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=5):
                pass
        def wait_status(expected):
            for attempt in range(30):
                request = urllib.request.Request('http://incident-agent:8080/incidents', headers={'Authorization': 'Bearer '+token})
                with urllib.request.urlopen(request, timeout=5) as response:
                    rows = json.load(response)
                matching = [r for r in rows if r['key'] == key]
                if matching and matching[0]['status'] == expected:
                    return matching[0]
                time.sleep(2)
            raise RuntimeError('Actual notification route did not deliver '+expected)
        send_alert(datetime.now(timezone.utc)+timedelta(minutes=5))
        firing = wait_status('firing')
        send_alert(datetime.now(timezone.utc))
        resolved = wait_status('resolved')
        assert firing['key'] == resolved['key']
        print('PASS: actual Alertmanager firing/recovery webhook delivery to persistent responder')
    print('PASS: private OTLP pipelines, Prometheus application/PostgreSQL metrics, trace, Loki logs and Grafana readiness')


if __name__ == '__main__':
    main()
