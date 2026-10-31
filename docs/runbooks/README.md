---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbooks (local observability stack)

Every alert rule in `docker/grafana/provisioning/alerting/rules-base.yaml` has a `runbook_url` pointing here. Alerts go from Grafana to the local ntfy (no Alertmanager, ADR D5). Evidence labels follow ADR D7.

| Alert | Rule `for` | Runbook | Drill record |
|---|---|---|---|
| `TargetDown` | 2m | [target-down.md](target-down.md) | [2026-10-18 target-down drill](records/2026-10-18-target-down-drill.md) (stop Loki) |
| `PrometheusUnreachable` | 2m | [alerting-pipeline.md](alerting-pipeline.md) | not drilled |
| `GrafanaAlertingFailures` | 0s | [alerting-pipeline.md](alerting-pipeline.md) | not drilled |
| `DiskSpaceLow` | 10m | [disk-space.md](disk-space.md) | proven by query only ([drill record](records/2026-10-18-target-down-drill.md), section 5) |
| `DiskWillFillIn24h` | 30m | [disk-space.md](disk-space.md) | proven by query only |
| `ApiLatencyP95High` | 2m | [api-latency-slo.md](api-latency-slo.md) | fire test: a Locust step above the knee (see the SLO record) |
| `ApiErrorRateHigh` | 2m | [api-latency-slo.md](api-latency-slo.md) | not drilled |
| `LogShippingErrors` | 10m | [log-shipping.md](log-shipping.md) | live proof: a stopped alloy, a fresh alloy against the 403, and a quiet stack (see the [alloy record](records/2026-10-28-alloy-log-shipping.md)) |
| `RedisDown` (cause alert) | 30s | [redis-down.md](redis-down.md) | the Redis-stop drill under load (see `records/`) |
| `AiWorkerLagHigh` | 2m | [ai-worker-lag.md](ai-worker-lag.md) | stop ai_worker while the engine publishes ([2026-10-26 record](records/2026-10-26-ai-worker-lag-alert.md)) |
| `AiWorkerPendingHigh` | 2m | [ai-worker-lag.md](ai-worker-lag.md) | not drilled |

Records of measured runs and drills are in `records/`.

## Common steps

- **Silence an alert:** Grafana, Alerting, Silences, New silence. Match `alertname` (and `job` or `mountpoint`) and set an end time. A silence stops the ntfy message, not the evaluation.
- **Escalation:** the owner. These alerts watch one local host; there is no on-call rotation.
- **Where the messages go:** the local ntfy on `127.0.0.1` (port `NTFY_PORT`, default 2586). The topic is in the gitignored `docker/secrets/ntfy_topic`; never paste it into a document.
