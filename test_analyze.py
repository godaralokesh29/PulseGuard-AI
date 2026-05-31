import asyncio
from backend.models.schemas import DecisionQuery
from backend.routes.decisions import get_vector_db, get_llm_engine
from backend.services.decision_engine import get_decision_engine

async def main():
    engine = get_decision_engine()
    vector_db = await get_vector_db()
    llm_engine = await get_llm_engine()
    
    query = DecisionQuery(
        error_type="database_timeout",
        metric_name="db_query_latency_ms",
        spike_percentage=450.0,
        tenant_id="payment_service",
        service_name="checkout",
        window_minutes=5,
        top_k=5
    )
    
    # We can just hit the LLM engine directly since the vector DB is populated at startup in main.py
    # But wait, vector DB requires the FastAPI app to start to populate. 
    # Let's just use the llm engine directly to test the new coral context stuff.
    
    anomaly_context = {
        "error_type": query.error_type,
        "metric_name": query.metric_name,
        "spike_percentage": query.spike_percentage,
        "tenant_id": query.tenant_id,
        "service_name": query.service_name,
        "window_minutes": query.window_minutes
    }
    
    res = await llm_engine.generate_decision(anomaly_context, [])
    import json
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
