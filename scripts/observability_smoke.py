"""Actual stack checks; run inside app container on the private telemetry network."""
import json
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
            log_query = urllib.parse.urlencode({'query': '{service_name="signaldesk"}', 'limit': 10})
            logs = json.loads(get('http://loki:3100/loki/api/v1/query_range?'+log_query))
            assert logs['data']['result'], 'No structured application logs'
            break
        except Exception:
            if attempt == 44:
                raise
            time.sleep(2)
    print('PASS: private OTLP pipelines, Prometheus application/PostgreSQL metrics, trace, Loki logs and Grafana readiness')


if __name__ == '__main__':
    main()
