---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS

## Title
ai_worker exposes its Redis Streams consumer-group lag and pending-message count as Prometheus gauges on a /metrics endpoint.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
These are ai_worker's saturation signals, so the planned SLO alerts have something concrete to fire on. The platform half (the scrape config in docker/prometheus.yml and the alert rule) is platform-planner's, filed by the lead.

## Scope
- ai_worker (src/observability/anomaly/worker.py) serves /metrics with:
  - consumer-group lag per stream and group;
  - the pending count, from the xpending_range data the consumer already reads (src/observability/stream/consumer.py).
- Reuse src/observability/prometheus_collector.py conventions for names, labels and registry.
- Out of the tick loop. It reads Redis only and never imports the engine; determinism is unaffected. Import contracts stay 17/0.
- Tests:
  - gauges reflect a fake stream's lag and pending count;
  - /metrics serves them;
  - no engine import.

## Out of Scope
- The dead-letter stream and retry cap (the user chose metrics only; a follow-up only if alerts show stuck messages).
- Prometheus config and alerts (platform).

## Acceptance Criteria
ai_worker's /metrics shows lag and pending gauges for each consumer group; tests and gates are green.

## Related Tickets
The platform scrape/alert ticket (lead-planner-u24).

## Related Docs
docs/engine/contracts/infrastructure_overview.md; docs/architecture/system_overview.md.

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS/ (plan, investigation, test_plan).

## Related Code Areas
src/observability/anomaly/worker.py; src/observability/stream/consumer.py; src/observability/prometheus_collector.py.

## Assumptions / Open Questions
Resolved: port 9108 (`AI_WORKER_METRICS_PORT`), expose-only; compose.yaml checked, no clash. Agreed with rpg-planner before the build.

## Implementation Notes
`src/observability/stream/lag_metrics.py`: a custom collector reads `XINFO GROUPS` at scrape time and yields `sim_stream_consumer_lag` and `sim_stream_pending_messages` per (stream, group) and `sim_stream_consumer_up`. When Redis cannot be read it yields up=0 and nothing else, so no stale value. An unknown lag (None) drops only the lag sample. It uses its own registry and `prometheus_client.start_http_server`, started from the worker's `__main__` for the redis backend only. compose.yaml gets the env var and `expose: 9108`; the scrape job and alert are platform's.

## Test Summary
`tests/unit/observability/stream/test_stream_lag_metrics.py` (12 tests, bad ports parametrised: lag/pending per stream and group, scrape-time reads, unknown lag, Redis down, unbuildable client, port default/env/bad values, /metrics over HTTP, no engine import). `tests/unit/observability/test_anomaly_worker.py` still passes.

## Files Changed
src/observability/stream/lag_metrics.py (new); src/observability/anomaly/worker.py; compose.yaml; docs/engine/contracts/infrastructure_overview.md; the new test file; this ticket and its stored artifacts.

## Completion Summary
ai_worker serves lag and pending gauges for each consumer group at ai_worker:9108/metrics. Metrics only; no dead-letter or retry change.
