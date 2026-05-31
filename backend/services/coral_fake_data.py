"""
Fake Coral data for hackathon demo.
Returns realistic-looking results for common SQL patterns so the demo
looks like Coral is pulling live data from PagerDuty, GitHub, Slack, Datadog, etc.
"""

import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _recent(minutes_ago: int = 0) -> str:
    return (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat() + "Z"


# ─── PagerDuty Incidents ───────────────────────────────────────────

PAGERDUTY_INCIDENTS = [
    {
        "id": "PD-2025-8841",
        "title": "Database connection pool exhausted — checkout-service",
        "status": "triggered",
        "urgency": "high",
        "service": "checkout-service",
        "created_at": _recent(12),
        "updated_at": _recent(3),
        "assigned_to": "oncall-sre-team",
    },
    {
        "id": "PD-2025-8839",
        "title": "Kafka consumer lag exceeding 50k on payment-events",
        "status": "acknowledged",
        "urgency": "high",
        "service": "payment-processor",
        "created_at": _recent(47),
        "updated_at": _recent(22),
        "assigned_to": "platform-eng",
    },
    {
        "id": "PD-2025-8835",
        "title": "Memory usage >90% on api-gateway pods",
        "status": "resolved",
        "urgency": "medium",
        "service": "api-gateway",
        "created_at": _recent(180),
        "updated_at": _recent(95),
        "assigned_to": "infra-team",
    },
    {
        "id": "PD-2025-8832",
        "title": "SSL certificate expiry warning — auth.pulseguard.io",
        "status": "triggered",
        "urgency": "low",
        "service": "auth-service",
        "created_at": _recent(300),
        "updated_at": _recent(290),
        "assigned_to": "security-team",
    },
    {
        "id": "PD-2025-8830",
        "title": "Elevated 5xx rate on /api/v1/transactions endpoint",
        "status": "acknowledged",
        "urgency": "high",
        "service": "transaction-service",
        "created_at": _recent(65),
        "updated_at": _recent(40),
        "assigned_to": "oncall-sre-team",
    },
]

# ─── GitHub Commits ────────────────────────────────────────────────

GITHUB_COMMITS = [
    {
        "sha": "a3f8c2d",
        "message": "fix: increase db connection pool size to 200",
        "author": "pranjwal",
        "repository": "pulseguard-backend",
        "branch": "hotfix/db-pool",
        "created_at": _recent(18),
        "files_changed": 2,
        "additions": 8,
        "deletions": 3,
    },
    {
        "sha": "e91b0f4",
        "message": "feat: add circuit breaker to payment gateway client",
        "author": "aarav",
        "repository": "pulseguard-backend",
        "branch": "main",
        "created_at": _recent(42),
        "files_changed": 5,
        "additions": 147,
        "deletions": 12,
    },
    {
        "sha": "7dc12e8",
        "message": "chore: bump kafka-python to 2.1.0",
        "author": "meera",
        "repository": "pulseguard-backend",
        "branch": "main",
        "created_at": _recent(90),
        "files_changed": 1,
        "additions": 1,
        "deletions": 1,
    },
    {
        "sha": "bc445a1",
        "message": "fix: memory leak in websocket connection handler",
        "author": "pranjwal",
        "repository": "pulseguard-backend",
        "branch": "hotfix/ws-memleak",
        "created_at": _recent(120),
        "files_changed": 3,
        "additions": 22,
        "deletions": 45,
    },
    {
        "sha": "f0923da",
        "message": "deploy: update k8s resource limits for api-gateway",
        "author": "devops-bot",
        "repository": "pulseguard-infra",
        "branch": "main",
        "created_at": _recent(200),
        "files_changed": 2,
        "additions": 6,
        "deletions": 6,
    },
]

# ─── GitHub Pull Requests ──────────────────────────────────────────

GITHUB_PULL_REQUESTS = [
    {
        "number": 342,
        "title": "Increase DB pool + add connection timeout",
        "state": "open",
        "author": "pranjwal",
        "repository": "pulseguard-backend",
        "created_at": _recent(15),
        "labels": ["hotfix", "database"],
        "review_status": "pending",
    },
    {
        "number": 340,
        "title": "Circuit breaker for external payment APIs",
        "state": "merged",
        "author": "aarav",
        "repository": "pulseguard-backend",
        "created_at": _recent(60),
        "labels": ["feature", "payments"],
        "review_status": "approved",
    },
    {
        "number": 338,
        "title": "Fix WebSocket memory leak on disconnect",
        "state": "merged",
        "author": "pranjwal",
        "repository": "pulseguard-backend",
        "created_at": _recent(130),
        "labels": ["bugfix", "websocket"],
        "review_status": "approved",
    },
]

# ─── Slack Messages ────────────────────────────────────────────────

SLACK_MESSAGES = [
    {
        "channel": "#incidents",
        "user": "pranjwal",
        "text": "🚨 seeing elevated db timeouts on checkout — investigating",
        "timestamp": _recent(10),
        "thread_reply_count": 4,
    },
    {
        "channel": "#incidents",
        "user": "aarav",
        "text": "looks like the connection pool got exhausted after the traffic spike. rolling out hotfix now",
        "timestamp": _recent(8),
        "thread_reply_count": 2,
    },
    {
        "channel": "#deployments",
        "user": "deploy-bot",
        "text": "✅ pulseguard-backend v2.4.1 deployed to production (hotfix/db-pool)",
        "timestamp": _recent(5),
        "thread_reply_count": 0,
    },
    {
        "channel": "#incidents",
        "user": "meera",
        "text": "kafka consumer lag is stabilizing — down to 12k from 50k peak",
        "timestamp": _recent(20),
        "thread_reply_count": 1,
    },
    {
        "channel": "#sre-oncall",
        "user": "pagerduty-bot",
        "text": "🔔 New incident PD-2025-8841: Database connection pool exhausted — checkout-service [HIGH]",
        "timestamp": _recent(12),
        "thread_reply_count": 3,
    },
]

# ─── Datadog Metrics ───────────────────────────────────────────────

DATADOG_METRICS = [
    {
        "metric": "system.cpu.utilization",
        "host": "checkout-prod-01",
        "value": 87.3,
        "unit": "percent",
        "timestamp": _recent(2),
        "tags": ["env:production", "service:checkout"],
    },
    {
        "metric": "system.mem.used_pct",
        "host": "api-gateway-prod-02",
        "value": 91.2,
        "unit": "percent",
        "timestamp": _recent(3),
        "tags": ["env:production", "service:api-gateway"],
    },
    {
        "metric": "db.pool.active_connections",
        "host": "postgres-primary",
        "value": 198,
        "unit": "connections",
        "timestamp": _recent(1),
        "tags": ["env:production", "db:checkout_db"],
    },
    {
        "metric": "kafka.consumer.lag",
        "host": "kafka-broker-01",
        "value": 14230,
        "unit": "messages",
        "timestamp": _recent(4),
        "tags": ["env:production", "topic:payment-events"],
    },
    {
        "metric": "http.server.error_rate",
        "host": "checkout-prod-01",
        "value": 4.7,
        "unit": "percent",
        "timestamp": _recent(2),
        "tags": ["env:production", "service:checkout", "status:5xx"],
    },
]

# ─── Coral internal tables ─────────────────────────────────────────

CORAL_TABLES = [
    {"table_name": "incidents", "schema_name": "pagerduty"},
    {"table_name": "commits", "schema_name": "github"},
    {"table_name": "pull_requests", "schema_name": "github"},
    {"table_name": "messages", "schema_name": "slack"},
    {"table_name": "metrics", "schema_name": "datadog"},
    {"table_name": "tables", "schema_name": "coral"},
    {"table_name": "deployments", "schema_name": "github"},
]


# ─── Query Matcher ─────────────────────────────────────────────────

def get_fake_coral_results(sql: str) -> List[Dict[str, Any]]:
    """
    Match a SQL query string against known patterns and return fake data.
    Very hacky pattern matching — it's a hackathon, fight me.
    """
    sql_lower = sql.lower().strip()

    # coral.tables
    if "coral.tables" in sql_lower:
        return _apply_limit(CORAL_TABLES, sql_lower)

    # PagerDuty
    if "pagerduty" in sql_lower:
        data = PAGERDUTY_INCIDENTS
        if "triggered" in sql_lower:
            data = [d for d in data if d["status"] == "triggered"]
        elif "acknowledged" in sql_lower:
            data = [d for d in data if d["status"] == "acknowledged"]
        return _apply_limit(data, sql_lower)

    # GitHub commits
    if "github.commits" in sql_lower or ("github" in sql_lower and "commit" in sql_lower):
        return _apply_limit(GITHUB_COMMITS, sql_lower)

    # GitHub PRs
    if "github.pull_requests" in sql_lower or ("github" in sql_lower and "pull" in sql_lower):
        return _apply_limit(GITHUB_PULL_REQUESTS, sql_lower)

    # Slack
    if "slack" in sql_lower:
        data = SLACK_MESSAGES
        if "#incidents" in sql_lower:
            data = [d for d in data if d["channel"] == "#incidents"]
        elif "#deployments" in sql_lower:
            data = [d for d in data if d["channel"] == "#deployments"]
        return _apply_limit(data, sql_lower)

    # Datadog
    if "datadog" in sql_lower:
        data = DATADOG_METRICS
        if "cpu" in sql_lower:
            data = [d for d in data if "cpu" in d["metric"]]
        elif "mem" in sql_lower:
            data = [d for d in data if "mem" in d["metric"]]
        elif "kafka" in sql_lower or "lag" in sql_lower:
            data = [d for d in data if "kafka" in d["metric"]]
        elif "error" in sql_lower:
            data = [d for d in data if "error" in d["metric"]]
        return _apply_limit(data, sql_lower)

    # Fallback — return some generic PagerDuty data so something shows up
    return _apply_limit(PAGERDUTY_INCIDENTS, sql_lower)


def _apply_limit(data: List[Dict[str, Any]], sql_lower: str) -> List[Dict[str, Any]]:
    """Extract LIMIT N from SQL and slice results."""
    match = re.search(r"limit\s+(\d+)", sql_lower)
    if match:
        limit = int(match.group(1))
        return data[:limit]
    return data
