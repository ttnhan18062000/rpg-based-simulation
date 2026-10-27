---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: AiWorkerLagHigh and AiWorkerPendingHigh (cause alerts)

Rules in `docker/grafana/provisioning/alerting/rules-worker.yaml` (group `worker`, folder Cause alerts, interval 30 s, severity warning). Source: `sim_stream_consumer_lag` and `sim_stream_pending_messages` from `ai_worker:9108` (job `ai_worker`, `src/observability/stream/lag_metrics.py`), aggregated `max by (stream, group)`. The expressions carry no comparison; the threshold is Grafana's step C (lag > 500 and pending > 100, set from the observation in the [2026-10-26 record](records/2026-10-26-ai-worker-lag-alert.md)).

| Rule | Fires when | `for` | `noDataState` |
|---|---|---|---|
| `AiWorkerLagHigh` | lag above 500, **or no lag series at all** | 2m | Alerting |
| `AiWorkerPendingHigh` | pending above 100 | 2m | OK |

`execErrState` is OK for both (a dead Prometheus is `PrometheusUnreachable`).

## Why NoData fires the lag alert
A stopped ai_worker serves no gauge, so there is no lag series, and that is the failure to catch: the stream backlog grows unseen. The same state occurs while Redis is down (the collector then yields only `sim_stream_consumer_up 0`); `RedisDown` is the cause there and this alert follows it. `TargetDown` for job `ai_worker` fires too when the target is gone.

## First three checks
1. `docker compose ps ai_worker`: stopped, restarting, or `unhealthy` (the healthcheck needs `sim_stream_consumer_up 1.0`)?
2. `docker compose logs --tail=100 ai_worker`; and `sim_stream_consumer_up` in Grafana Explore: 0 means Redis did not answer the worker's query.
3. `docker compose exec redis redis-cli XINFO GROUPS simulation:events`: `lag` is undelivered entries, `pending` is delivered and unacknowledged.

## Recovery
`docker compose up -d ai_worker`. The worker resumes its consumer group; lag drains at the worker's rate, and the alert resolves after the next evaluation below the threshold. Pending entries left by a crashed worker are not re-delivered by this alert's fix; report them to the owner of the consumer (rpg) if pending stays high with the worker healthy.

## Silence and escalate
See the [index](README.md). Silence only for planned maintenance. Escalate to the owner if lag keeps rising with a healthy worker.
