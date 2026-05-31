import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from prometheus_client import make_asgi_app
from fastapi import FastAPI
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def setup_observability(app: FastAPI):
    """Sets up OpenTelemetry tracing and Prometheus metrics for FastAPI."""
    try:
        # Prometheus Metrics
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Mounted Prometheus metrics at /metrics")

        # OpenTelemetry Tracing (Skip if running locally without Jaeger to prevent spam)
        if "localhost" not in settings.otel_exporter_otlp_endpoint:
            resource = Resource.create(attributes={
                "service.name": settings.app_name,
                "service.version": settings.app_version
            })
            
            provider = TracerProvider(resource=resource)
            otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
            processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(processor)
            
            trace.set_tracer_provider(provider)
        else:
            logger.info("Skipping OpenTelemetry export (local dev mode detected)")
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"OpenTelemetry instrumentation enabled (Exporting to {settings.otel_exporter_otlp_endpoint})")

    except Exception as e:
        logger.warning(f"Failed to setup observability stack: {e}")
