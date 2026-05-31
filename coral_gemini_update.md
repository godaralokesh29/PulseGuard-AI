# Coral & Gemini 3.5 Integration Update

## What We Did

1. **Coral Core Integration**
   - Wrote `backend/services/coral_client.py`: A lightweight asynchronous Python wrapper that executes Coral SQL queries directly via the CLI and parses the JSON output.
   - Updated `backend.Dockerfile`: Added a step to automatically download and install the Coral CLI binary during the container build process so it runs natively alongside the backend.
   - Fixed `test_coral.py` to query `coral.tables` instead of a broken PagerDuty schema, verifying Coral is successfully connected.

2. **Gemini 3.5 Flash Migration**
   - **Replaced OpenAI with Google GenAI SDK**: Stripped out OpenAI entirely and moved to the modern `google-genai` package.
   - **Updated `llm_engine.py`**: Refactored the `LLMEngine` to use `gemini-3.5-flash`. It now uses `response_schema` to guarantee that the LLM continues outputting the strict Pydantic JSON structure (`DecisionStructuredOutput`) the system expects.
   - **Dynamic Context Injection**: Wired the new Coral client directly into the LLM engine. Right before the LLM evaluates an anomaly, the backend pulls data via Coral to inject into the LLM context.

3. **Hackathon Local Setup & Bug Fixes**
   - Created `run_local.sh` to run the frontend (Next.js) and backend (FastAPI) concurrently without Docker.
   - Installed missing `google-genai` dependency using `uv pip`.
   - Fixed a `WebSocketDisconnect` loop bug in `backend/routes/ws_endpoints.py` that was spamming the server.
   - Patched `backend/services/pipeline.py` to gracefully handle missing Kafka clusters so the app can boot locally.
   - Fixed Next.js hydration mismatch issues in `app/layout.tsx`.

## What Needs To Be Done Next

1. **Configure Real Data Sources in Coral**
   - We need to configure actual local sources in Coral (`~/.coral/sources.yml`) like GitHub, Slack, or Datadog. Right now, Coral is working, but it only has access to its internal schemas. 

2. **Dynamic SQL Generation by the LLM**
   - Currently, `llm_engine.py` hardcodes a query (e.g. to PagerDuty) before running the LLM prompt.
   - **Task**: Upgrade the LLM engine to let the Gemini model decide *which* SQL query to run dynamically based on the anomaly (e.g., querying GitHub if it's a deployment anomaly, or Datadog if it's latency).

3. **Restore Kafka Streaming (Post-Hackathon)**
   - The Kafka pipeline startup is currently wrapped in a `try/except` block because we aren't running Docker.
   - **Task**: Spin up a local Kafka cluster or run it via Docker Compose so the Flink telemetry pipeline can actually produce anomaly messages.

4. **Full MCP Server Migration (Optional)**
   - If the `subprocess` CLI integration (`coral_client.py`) becomes too slow, upgrade to running Coral natively as a persistent MCP (Model Context Protocol) server for bidirectional tool usage.
