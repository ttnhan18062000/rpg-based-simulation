---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: TargetDown

Rule `TargetDown` (group `base`): `min by (job) (up) < 1` for 2m, evaluated every 1m. Severity critical. `noDataState: OK` and `execErrState: OK` (a vanished series is a config change; a dead Prometheus is `PrometheusUnreachable`). Expected detection: up to 1m evaluation + 2m `for` + 30s group wait, so about 3 to 4 minutes. Measured in the 2026-10-18 drill ([record](records/2026-10-18-target-down-drill.md)): the firing message arrived 3 m 39 s after the stop, and the resolved message about 4 m 42 s after the restart (the group_interval wait).

## What it means
Prometheus could not scrape the target named in the `job` label (`prometheus`, `grafana`, `loki`, `tempo`, `node-exporter`, `ntfy`, `rpg-backend`, `redis`, `promtail`, `ai_worker`). The service may be down, restarting, or failing its metrics endpoint. The backend is not scraped yet (`backend:9109` comes with rpg R1, #622).

## First three checks
1. `docker compose --profile observability ps`: is the service running and healthy?
2. Prometheus targets page (`http://127.0.0.1:9090/targets`): the error text of the failing target.
3. `docker compose --profile observability logs --tail=100 <service>`: a crash, an out-of-memory kill (`docker inspect <container> --format '{{.State.OOMKilled}}'`), or a config error.

## Known causes
- The service was stopped on purpose (this is the drill: `docker compose stop loki`).
- Out of memory against its `mem_limit`.
- A config change the service rejects at start (Tempo and Grafana both did in earlier runs).
- Loki has no healthcheck (its image has no shell); `up{job="loki"}` is its probe.

## Mitigation
Fix the cause, then `docker compose --profile observability up -d <service>`. The alert resolves after the next successful scrape and sends a resolved message.

## Silence and escalate
Silence only for planned maintenance (see the README). Escalate to the owner if a service will not start after one restart.
