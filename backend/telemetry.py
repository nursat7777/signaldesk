"""Bounded, privacy-preserving OTLP telemetry. No payloads, IDs or SQL values."""
import json
import logging
import os
import resource
import time
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import Observation
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from sqlalchemy import event

BUSINESS = {
    'createClient': 'client_create', 'updateClient': 'client_update',
    'createCampaign': 'campaign_create', 'updateCampaign': 'campaign_update',
    'saveMetric': 'daily_metric_save', 'getReport': 'report_generate',
    'createUser': 'user_create', 'updateUser': 'user_update',
    'setAssignments': 'assignment_update',
}


def resident_memory():
    try:
        with open('/proc/self/statm') as stream:
            return int(stream.read().split()[1]) * os.sysconf('SC_PAGE_SIZE')
    except OSError:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


class JsonFormatter(logging.Formatter):
    def format(self, record):
        # Deliberate allowlist: never format arbitrary messages, headers or exceptions.
        return json.dumps({key: getattr(record, key, None) for key in
                          ('event', 'route', 'method', 'status', 'duration', 'trace_id', 'span_id')})


class Telemetry:
    def __init__(self, reader=None, span_processor=None, log_processor=None):
        env = os.getenv('APP_ENV', 'local')
        if env not in ('local', 'test', 'development', 'production'):
            raise ValueError('Invalid APP_ENV')
        res = Resource.create({'service.name': 'signaldesk', 'deployment.environment.name': env})
        endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', '').rstrip('/')
        readers = [reader] if reader else []
        if endpoint and not reader:
            readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint+'/v1/metrics', timeout=3), export_interval_millis=10000))
        self.meter_provider = MeterProvider(resource=res, metric_readers=readers)
        self.tracer_provider = TracerProvider(resource=res)
        self.logger_provider = LoggerProvider(resource=res)
        if span_processor:
            self.tracer_provider.add_span_processor(span_processor)
        elif endpoint:
            self.tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint+'/v1/traces', timeout=3), max_queue_size=512))
        if log_processor:
            self.logger_provider.add_log_record_processor(log_processor)
        elif endpoint:
            self.logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint+'/v1/logs', timeout=3), max_queue_size=512))
        self.tracer = self.tracer_provider.get_tracer('signaldesk')
        meter = self.meter_provider.get_meter('signaldesk')
        self.requests = meter.create_counter('signaldesk_http_requests', description='Completed HTTP requests')
        self.duration = meter.create_histogram('signaldesk_http_duration', unit='s')
        self.operations = {op: meter.create_counter('signaldesk_'+op, description='Business operation attempts by outcome') for op in set(BUSINESS.values())}
        self.failures = meter.create_counter('signaldesk_business_failures')
        self.denials = meter.create_counter('signaldesk_permission_denials')
        meter.create_observable_gauge('signaldesk_process_memory', callbacks=[lambda _: [Observation(resident_memory())]], unit='By')
        meter.create_observable_counter('signaldesk_process_cpu', callbacks=[lambda _: [Observation(time.process_time())]], unit='s')
        error_logger = logging.getLogger('uvicorn.error')
        if not any(isinstance(f, ExceptionRedactionFilter) for f in error_logger.filters):
            error_logger.addFilter(ExceptionRedactionFilter())
        self.logger = logging.Logger('signaldesk.telemetry')
        console = logging.StreamHandler()
        console.setFormatter(JsonFormatter())
        self.logger.addHandler(console)
        if endpoint or log_processor:
            handler = LoggingHandler(logger_provider=self.logger_provider)
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)

    def shutdown(self):
        self.meter_provider.shutdown()
        self.tracer_provider.shutdown()
        self.logger_provider.shutdown()

    def instrument_database(self, engine):
        @event.listens_for(engine, 'before_cursor_execute')
        def before(conn, cursor, statement, parameters, context, executemany):
            # Record only the SQL verb; never the query or parameter values.
            verb = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else 'SQL'
            verb = verb if verb in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'BEGIN', 'COMMIT') else 'SQL'
            context._sd_span = self.tracer.start_span('database '+verb, kind=trace.SpanKind.CLIENT, attributes={'db.operation.name': verb, 'db.system.name': engine.dialect.name})

        @event.listens_for(engine, 'after_cursor_execute')
        def after(conn, cursor, statement, parameters, context, executemany):
            context._sd_span.end()

        @event.listens_for(engine, 'handle_error')
        def error(context):
            span = getattr(context.execution_context, '_sd_span', None)
            if span:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.end()


class TelemetryMiddleware:
    def __init__(self, app, telemetry):
        self.app, self.t = app, telemetry

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        method = scope['method'] if scope['method'] in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD') else 'OTHER'
        started, status = time.monotonic(), 500
        headers = {k.decode('latin1'): v.decode('latin1') for k, v in scope.get('headers', []) if k in (b'traceparent', b'tracestate')}
        with self.t.tracer.start_as_current_span('HTTP', context=extract(headers), kind=trace.SpanKind.SERVER, record_exception=False, set_status_on_exception=False) as span:
            async def wrapped(message):
                nonlocal status
                if message['type'] == 'http.response.start':
                    status = message['status']
                await send(message)
            try:
                await self.app(scope, receive, wrapped)
            finally:
                elapsed = time.monotonic() - started
                route_obj = scope.get('route')
                route = getattr(route_obj, 'path', 'unmatched')
                # The static catch-all has a fixed path, never an attacker-supplied URL.
                attrs = {'http.route': route, 'http.request.method': method, 'http.response.status_code': status}
                span.update_name(method+' '+route)
                span.set_attributes(attrs)
                if status >= 500:
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                self.t.requests.add(1, attrs)
                self.t.duration.record(elapsed, attrs)
                operation = BUSINESS.get(getattr(route_obj, 'operation_id', None))
                outcome = 'success' if status < 400 else 'failure'
                if operation:
                    self.t.operations[operation].add(1, {'outcome': outcome})
                    if status >= 400:
                        self.t.failures.add(1, {'operation': operation})
                if status == 403:
                    self.t.denials.add(1, {'http.route': route})
                context = span.get_span_context()
                self.t.logger.info('request_completed', extra={'event': 'request_completed', 'route': route, 'method': method, 'status': status, 'duration': elapsed, 'trace_id': format(context.trace_id, '032x'), 'span_id': format(context.span_id, '016x')})


class ExceptionRedactionFilter(logging.Filter):
    """Keep Uvicorn failures visible without exception strings containing SQL values."""
    def filter(self, record):
        if record.exc_info:
            record.msg = 'Unhandled application error; inspect correlated request status and trace'
            record.args = ()
            record.exc_info = None
            record.exc_text = None
        return True
