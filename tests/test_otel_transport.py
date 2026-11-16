"""Real HTTP/protobuf OTLP exporters, independent of the Collector runtime."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from fastapi.testclient import TestClient
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from backend.app import create_app
from backend.core import MemoryRepository, Settings
from backend.telemetry import Telemetry


def test_real_http_otlp_three_signals(monkeypatch):
    received = {}
    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self):
            received.setdefault(self.path, []).append(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(200)
            self.end_headers()
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://127.0.0.1:'+str(server.server_port))
    monkeypatch.setenv('OTEL_TRACES_SAMPLER', 'always_on')
    monkeypatch.setenv('APP_ENV', 'test')
    t = Telemetry()
    try:
        with TestClient(create_app(Settings(), MemoryRepository(), t)) as client:
            assert client.get('/api/auth/status?private=DO_NOT_EXPORT').status_code == 200
            t.meter_provider.force_flush()
            t.tracer_provider.force_flush()
            t.logger_provider.force_flush()
        trace = ExportTraceServiceRequest.FromString(received['/v1/traces'][0])
        metrics = ExportMetricsServiceRequest.FromString(received['/v1/metrics'][0])
        logs = ExportLogsServiceRequest.FromString(received['/v1/logs'][0])
        assert trace.resource_spans[0].scope_spans[0].spans[0].name == 'GET /api/auth/status'
        assert any(m.name == 'signaldesk_http_requests' for r in metrics.resource_metrics for s in r.scope_metrics for m in s.metrics)
        assert logs.resource_logs[0].scope_logs[0].log_records[0].trace_id
        assert all(b'DO_NOT_EXPORT' not in payload for payloads in received.values() for payload in payloads)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
