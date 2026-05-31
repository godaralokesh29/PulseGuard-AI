import logging
import asyncio
import json
from typing import Optional
from backend.services.kafka_client import kafka_client
from backend.models.schemas import StreamingAnomalyCreate

logger = logging.getLogger(__name__)

class PipelineService:
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        try:
            # We add a timeout here because AIOKafka can hang indefinitely if the broker is unreachable,
            # which would cause the entire API request to hang.
            await asyncio.wait_for(kafka_client.start_producer(), timeout=2.0)
            await asyncio.wait_for(kafka_client.start_consumer(
                topic="telemetry_anomalies",
                group_id="fastapi_backend",
                callback=self.handle_anomaly
            ), timeout=2.0)
            logger.info("Pipeline service started with Kafka Integration.")
        except (Exception, asyncio.TimeoutError) as e:
            logger.warning(f"Kafka unavailable, running without it. Error: {e}")

    async def stop(self):
        self.is_running = False
        await kafka_client.stop_producer()
        logger.info("Pipeline service stopped.")

    async def ingest_telemetry(self, telemetry: dict):
        """Sends raw telemetry to Kafka for Flink to process."""
        try:
            if kafka_client.producer:
                await kafka_client.send_message("telemetry_raw", telemetry)
            else:
                # [HACKATHON MOCK] Simulate Flink processing the raw telemetry
                # into an anomaly and sending it back to handle_anomaly
                logger.info("[DEMO] Kafka unavailable. Simulating Flink processing pipeline...")
                asyncio.create_task(self._simulate_flink(telemetry))
        except Exception as e:
            logger.error(f"Failed to ingest telemetry: {e}")
            
    async def _simulate_flink(self, telemetry: dict):
        """Mock Flink job for the hackathon demo."""
        await asyncio.sleep(2) # Simulate processing time
        # Convert raw telemetry to a Flink anomaly output format
        anomaly = {
            "tenant_id": telemetry.get("tenant_id"),
            "service_name": telemetry.get("service_name"),
            "metric_name": telemetry.get("metric_name"),
            "spike_percentage": telemetry.get("spike_percentage")
        }
        await self.handle_anomaly(anomaly)

    async def handle_anomaly(self, anomaly_data: dict):
        """Called when Flink detects an anomaly and produces to Kafka."""
        logger.warning(f"Anomaly detected from Flink: {anomaly_data}")
        # Here we would integrate with the decision engine
        from backend.services.decision_engine import get_decision_engine
        
        # Construct StreamingAnomalyCreate from Flink output
        anomaly_model = StreamingAnomalyCreate(
            tenant_id=anomaly_data.get("tenant_id", "default"),
            service_name=anomaly_data.get("service_name", "unknown"),
            error_type="Spike Detected",
            metric_name=anomaly_data.get("metric_name", "unknown"),
            baseline_value=0.0, # Not passed by minimal Flink job above
            current_value=0.0,  
            spike_percentage=anomaly_data.get("spike_percentage", 0.0),
            window_minutes=1
        )
        
        # Analyze using real LLM and VectorDB
        engine = get_decision_engine()
        
        # Notify the UI that an anomaly arrived first
        from backend.services.notification import get_notification_service, Decision
        notif_service = get_notification_service()
        
        await notif_service.notify_anomaly(
            tenant_id=anomaly_model.tenant_id,
            service_name=anomaly_model.service_name,
            error_type=anomaly_model.error_type,
            spike_percentage=anomaly_model.spike_percentage,
            metric_name=anomaly_model.metric_name,
            channels=["websocket"]
        )

        # Build query for the decision engine
        decision_result = await engine.evaluate(
            query=f"{anomaly_model.error_type} spike {anomaly_model.spike_percentage}% on {anomaly_model.service_name}",
            collection_name="historical_rcas"
        )
        
        # Broadcast decision over websockets
        # engine.evaluate returns a dict, we need to map it to a Decision dataclass
        decision_obj = Decision(
            id=decision_result.get("id", "demo"),
            matched_incident=decision_result.get("matched_incident", "Live Anomaly Detected"),
            symptom=f"{anomaly_model.error_type} spike detected",
            recommended_action=decision_result.get("llm_response", "Please check logs manually."),
            confidence_score=decision_result.get("confidence", 0.5),
            citations=[],
            latency_ms=decision_result.get("latency_ms", 0),
            generated_at=decision_result.get("triggered_at", ""),
            tenant_id=anomaly_model.tenant_id,
            service_name=anomaly_model.service_name
        )
        
        await notif_service.notify_decision(decision_obj, channels=["websocket"])

_pipeline_instance: Optional[PipelineService] = None

async def get_pipeline() -> PipelineService:
    global _pipeline_instance
    if not _pipeline_instance:
        _pipeline_instance = PipelineService()
        await _pipeline_instance.start()
    return _pipeline_instance

async def shutdown_pipeline():
    global _pipeline_instance
    if _pipeline_instance:
        await _pipeline_instance.stop()
        _pipeline_instance = None
