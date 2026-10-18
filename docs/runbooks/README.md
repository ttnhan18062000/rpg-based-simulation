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
| `TargetDown` | 2m | [target-down.md](target-down.md) | the target-down drill in `records/` (stop Loki) |
| `PrometheusUnreachable` | 2m | [alerting-pipeline.md](alerting-pipeline.md) | not drilled |
| `GrafanaAlertingFailures` | 0s | [alerting-pipeline.md](alerting-pipeline.md) | not drilled |
| `DiskSpaceLow` | 10m | [disk-space.md](disk-space.md) | proven by query only (see the drill record) |
| `DiskWillFillIn24h` | 30m | [disk-space.md](disk-space.md) | proven by query only |

Records of measured runs and drills are in `records/`.

## Common steps

- **Silence an alert:** Grafana, Alerting, Silences, New silence. Match `alertname` (and `job` or `mountpoint`) and set an end time. A silence stops the ntfy message, not the evaluation.
- **Escalation:** the owner. These alerts watch one local host; there is no on-call rotation.
- **Where the messages go:** the local ntfy on `127.0.0.1` (port `NTFY_PORT`, default 2586). The topic is in the gitignored `docker/secrets/ntfy_topic`; never paste it into a document.
