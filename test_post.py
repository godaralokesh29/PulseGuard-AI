import requests
import json

payload = {
  "error_type": "database_timeout",
  "metric_name": "db_query_latency_ms",
  "spike_percentage": 450,
  "tenant_id": "payment_service",
  "service_name": "checkout",
  "window_minutes": 5,
  "top_k": 5
}

try:
    res = requests.post("http://localhost:8000/api/v1/decisions/analyze", json=payload)
    print("Analyze Status:", res.status_code)
    print("Analyze Response:", res.text)
except Exception as e:
    print("Analyze Error:", e)

payload2 = {
  "tenant_id": "payment_service",
  "service_name": "checkout",
  "error_type": "database_timeout",
  "metric_name": "db_connection_pool",
  "baseline_value": 60,
  "current_value": 330,
  "spike_percentage": 450,
  "window_minutes": 5
}
try:
    res = requests.post("http://localhost:8000/api/v1/decisions/stream-anomaly", json=payload2)
    print("Stream Status:", res.status_code)
    print("Stream Response:", res.text)
except Exception as e:
    print("Stream Error:", e)

