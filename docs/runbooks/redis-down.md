---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: RedisDown (cause alert)

**Cause alert, added 2026-10-18 by lead review.** This is not the step-3 SLO alert. Rule `RedisDown` (group `cause`, `docker/grafana/provisioning/alerting/rules-redis.yaml`): `redis_up == 0` from `redis_exporter` (job `redis`), `for: 30s`, group interval 30 s, severity warning. `noDataState: OK` and `execErrState: OK`: an exporter that is down is `TargetDown` for job `redis` ([target-down.md](target-down.md)), and a dead Prometheus is `PrometheusUnreachable` ([alerting-pipeline.md](alerting-pipeline.md)). Expected detection: up to 30 s evaluation + 30 s `for` + 30 s notification group wait, so about 1.5 to 2 minutes.

## Why this alert exists
From a code read (2026-10-18), the API SLO stays green while Redis is down: `/health` reports engine liveness only, the read routes do not use Redis, and the stream adapter publishes from a background queue with short timeouts and drops what it cannot send. Events are still lost (the anomaly stream and ai_worker's input), and nothing else alerts on that. These statements are the drill's hypotheses; the drill record ([records/](records/)) marks each one confirmed or refuted.

## What is lost while Redis is down, and what is not
- **Lost (to be confirmed by the drill):** events published to the stream during the outage are dropped, not replayed afterwards. ai_worker has no new input while Redis is down.
- **Not lost:** the API keeps serving reads and the engine keeps ticking. `ApiLatencyP95High` and `ApiErrorRateHigh` are expected to stay quiet, which is the reason this alert exists.

## First three checks
1. `docker compose ps redis redis-exporter` and `docker compose logs --tail=100 redis`: is Redis stopped, restarting or out of memory?
2. `redis_up` in Grafana Explore (prometheus): 0 means the exporter cannot reach Redis; if the `redis` target itself is down, that is a `TargetDown` for the exporter.
3. Backend logs in Loki (`{container=~".*backend.*"}`): stream publish errors or timeouts from the adapter.

## Recovery
`docker compose start redis` (or `up -d redis`). The alert resolves after the next evaluation with `redis_up == 1` and sends a resolved message. The ai_worker is expected to reconnect by itself (drill hypothesis; confirm in the record).

## After recovery: check the backlog
The events published during the outage are gone, so there is nothing to replay. Check that the stream is moving again: `redis_stream_length` (from the exporter) for `simulation:events` rises again, ai_worker's logs show it consuming, and `docker compose exec redis redis-cli XLEN simulation:events` grows. Record the outage window so a downstream gap can be explained.

## Silence and escalate
See the [index](README.md) for the silence steps. Silence only for planned maintenance. Escalate to the owner if Redis does not come back after a restart or if the data volume looks corrupt (do not delete `redis_data` without the owner).
