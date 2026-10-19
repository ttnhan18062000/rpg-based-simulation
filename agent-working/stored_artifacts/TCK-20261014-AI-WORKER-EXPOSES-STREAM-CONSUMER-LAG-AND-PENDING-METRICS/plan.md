---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS
artifact_type: plan
tags: []
---

# plan — TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS

1. New `src/observability/stream/lag_metrics.py`: `StreamLagCollector` (XINFO GROUPS at scrape time), port from `AI_WORKER_METRICS_PORT` (default 9108), `start_lag_metrics_server`.
2. Start it from the worker's `__main__` when the backend is redis.
3. compose.yaml: the env var and `expose` for ai_worker (no host publish).
4. Tests with a fake Redis; docs line in the infrastructure overview.
