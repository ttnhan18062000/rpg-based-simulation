---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: LogShippingErrors

Rule `LogShippingErrors` (group `base`): `sum(rate(loki_internal_log_messages_total{job="promtail",level="error"}[5m]))` greater than 0, for 10m, evaluated every 1m. Severity warning. `noDataState: Alerting` (the series exists at 0 from a fresh promtail start, so no data means the series vanished: promtail is not scraped or its metrics are gone), `execErrState: OK` (a dead Prometheus is `PrometheusUnreachable`). The expression carries no comparison on purpose: a healthy promtail returns 0 and stays Normal.

## What it means
Promtail is logging errors continuously. Every failed Docker discovery refresh and every failed push to Loki writes one error-level line, and promtail counts its own log lines by level. **It fires on errors that recur at least every 5 minutes for 10 minutes; isolated errors further apart do not fire.** While it fires, logs are not reaching Loki (or only some are), so the Loki checks in the other runbooks find nothing.

## First three checks
1. `docker compose --profile observability logs --tail=100 promtail`: the repeated error line decides the cause.
   - `error while computing network labels ... 403 Forbidden`: the `docker-socket-proxy` allow-list does not include `/networks`. `NETWORKS=1` must be set on the proxy in `compose.yaml` (decision: owner via lead-planner, 2026-10-20; see the comment on the proxy). Recreate the proxy and promtail after a change.
   - `error while listing containers` or `Cannot connect`: the proxy is down or restarting; check `docker compose ps docker-socket-proxy`.
   - push errors (`error sending batch`, status 429 or 5xx): Loki is down, not ready or rate limiting; check `curl -s http://127.0.0.1:3100/ready`.
2. Promtail's own view: `docker compose exec promtail bash -c "exec 3<>/dev/tcp/localhost/9080; printf 'GET /targets HTTP/1.0\r\n\r\n' >&3; cat <&3"` shows the Docker target count (`N/M ready`); 0/0 with the repeated error means discovery is broken.
3. Is shipping actually moving: `promtail_sent_entries_total` rising (Prometheus job `promtail`), or a fresh backend line in Loki (`{container="platform-backend-1"}`). Loki keeps old lines, so old labels and old lines prove nothing; only new lines or a rising counter do.

## Known causes
- The proxy lost `NETWORKS=1` (a regression of the compose file).
- Promtail restarted while the proxy was recreated; the per-container log streams die with the old proxy and the targets must be rediscovered.
- Loki unavailable (restarting, out of memory) for longer than promtail's retries.

## Mitigation
Fix the cause, then `docker compose --profile observability up -d --force-recreate docker-socket-proxy promtail`. The error counter stops rising; the alert resolves after the 5 minute rate window clears.

## Not this alert
Promtail down or not scraped: `TargetDown{job="promtail"}` ([target-down.md](target-down.md)). No logs because the stack is idle: not an error, and the alert does not fire on zero sent entries.

## Silence and escalate
See the [index](README.md). Escalate to the owner if logs do not return after a recreate.
