---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: LogShippingErrors

Rule `LogShippingErrors` (group `base`): `sum(rate(prometheus_sd_refresh_failures_total{job="alloy"}[5m])) + (sum(rate(loki_write_batch_retries_total{job="alloy"}[5m])) or vector(0)) + sum(rate(loki_write_dropped_entries_total{job="alloy"}[5m]))` greater than 0, for 10m, evaluated every 1m. Severity warning. `noDataState: Alerting` (`prometheus_sd_refresh_failures_total` exists at 0 from a fresh alloy start, so no data means the series vanished: alloy is not scraped or its metrics are gone), `execErrState: OK` (a dead Prometheus is `PrometheusUnreachable`). The expression carries no comparison on purpose: a healthy alloy returns 0 and stays Normal.

## What it means
Alloy keeps failing to discover containers or to push to Loki. The rule adds three rates: failed Docker discovery refreshes (`prometheus_sd_refresh_failures_total`, one per failed 5 s refresh), Loki push retries (`loki_write_batch_retries_total`) and entries dropped after all retries (`loki_write_dropped_entries_total`). **It fires on failures that recur at least every 5 minutes for 10 minutes; isolated failures further apart do not fire.** While it fires, logs are not reaching Loki (or only some are), so the Loki checks in the other runbooks find nothing.

## First three checks
1. `docker compose --profile observability logs --tail=100 alloy`: the repeated error line decides the cause.
   - `error while computing network labels ... 403 Forbidden`: the `docker-socket-proxy` allow-list does not include `/networks`. `NETWORKS=1` must be set on the proxy in `compose.yaml` (decision: owner via lead-planner, 2026-10-20; see the comment on the proxy). Recreate the proxy and alloy after a change.
   - `error while listing containers` or `Cannot connect to the Docker daemon`: the proxy is down or restarting; check `docker compose ps docker-socket-proxy`.
   - push errors (`final error sending batch`, retries, status 429 or 5xx): Loki is down, not ready or rate limiting; check `curl -s http://127.0.0.1:3100/ready`.
2. Alloy's own view: `docker compose exec alloy bash -c "exec 3<>/dev/tcp/localhost/12345; printf 'GET /api/v0/web/components/discovery.docker.containers HTTP/1.0\r\n\r\n' >&3; cat <&3"` lists the discovered targets (this project's containers only); an empty list with the repeated error means discovery is broken. The same view is at http://127.0.0.1:12345 only if you publish the port yourself (the compose file does not).
3. Is shipping actually moving: `loki_write_sent_entries_total` rising (Prometheus job `alloy`), or a fresh backend line in Loki (`{container="platform-backend-1"}`). Loki keeps old lines, so old labels and old lines prove nothing; only new lines or a rising counter do.

## Known causes
- The proxy lost `NETWORKS=1` (a regression of the compose file).
- Alloy running while the proxy was recreated; the per-container log streams die with the old proxy, so recreate alloy after the proxy.
- Loki unavailable (restarting, out of memory) for longer than Alloy's push retries (`max_backoff_retries` 10).

## Mitigation
Fix the cause, then `docker compose --profile observability up -d --force-recreate docker-socket-proxy alloy`. The error counter stops rising; the alert resolves after the 5 minute rate window clears.

## Not this alert
Alloy down or not scraped: `TargetDown{job="alloy"}` ([target-down.md](target-down.md)). No logs because the stack is idle: not an error, and the alert does not fire on zero sent entries.

## Silence and escalate
See the [index](README.md). Escalate to the owner if logs do not return after a recreate.

## Restart behaviour
Alloy keeps its read offsets inside the container (`--storage.path`, no volume), as Promtail kept them in `/tmp`. After a recreate it reads each retained container log again; see the [2026-10-28 record](records/2026-10-28-alloy-log-shipping.md) for what Loki did with the replayed lines.
