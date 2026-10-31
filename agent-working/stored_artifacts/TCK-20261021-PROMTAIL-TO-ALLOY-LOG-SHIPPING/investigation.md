---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING
phase: investigation
date: 2026-10-28
tags: [observability, platform]
---

# Investigation: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING

Probes ran 2026-10-28 on host ubuntu with the pinned image; raw output was read from the commands, summary below.

## 1. Promtail end of support
Grafana's migration guide (grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/) states Promtail reached end of life on 2026-03-02 and is no longer maintained. Promtail 3.6.8 therefore already receives no fixes; the ticket's P3 understates the exposure but nothing breaks today.

## 2. Alloy release and pin
`gh release list --repo grafana/alloy` (2026-10-28): v1.21.2 (10-22), v1.21.1 (10-21), v1.21.0 (10-19), v1.20.1 (2026-09-28). The newest release at least 14 days old is **v1.20.1** (30 days). Multi-arch OCI index digest (`docker buildx imagetools inspect`): `sha256:2aa2099af76c0098d4af7a4d6e48f86cb66dc1a000222ad927a1c67c6542d13f` (amd64, arm64, ppc64le, s390x). The v1.20.1 notes are loki fixes only (batch size estimate, byte counters), no breaking change.

## 3. Docker discovery against the proxy
Upstream docs (discovery.docker) do not name the endpoints, so this was probed: Alloy v1.20.1 against `docker-socket-proxy:v0.4.1`.
- `NETWORKS=1 CONTAINERS=1 POST=0`: discovery works, 0 error lines, `loki_source_docker_target_entries_total` rose to 76 in 15 s.
- `NETWORKS=0`: every refresh logs `error while computing network labels ... 403 Forbidden`, the same failure as Promtail's (same Prometheus moby discovery code).
So Alloy needs exactly CONTAINERS and NETWORKS (container list/inspect/logs and GET /networks): **no further proxy endpoint, no stop point**. `loki.source.docker` talks to the same proxy for logs, so the Alloy container needs no socket mount.

## 4. Image probe tools
`docker run --entrypoint sh`: bash, sh, cat, head, grep, timeout exist; wget, curl, nc and busybox do not. The /dev/tcp bash probe of today's Promtail healthcheck works unchanged; Alloy readiness is `GET /-/ready` on the HTTP server (200 verified on port 12345).

## 5. Error metric for LogShippingErrors
Alloy has no counterpart to `loki_internal_log_messages_total`. Metrics on a fresh start (probe, healthy proxy): 
- `prometheus_sd_refresh_failures_total{mechanism="docker"}` exists at **0** and rose to 3 in 15 s under the 403 case (fresh start, NETWORKS=0). It counts every failed discovery refresh.
- `loki_write_dropped_entries_total{reason=...}` (five reasons) exists at 0 from the start; `loki_write_batch_retries_total` appears only after the first retry (value 4 when Loki was unreachable), so it is absent from a healthy fresh start.
- `loki_source_docker_target_parsing_errors_total` exists at 0 (not a delivery failure).
A series that exists at 0 from a fresh start is available, so no stop point. Design: `sum(rate(prometheus_sd_refresh_failures_total{job="alloy"}[5m])) + (sum(rate(loki_write_batch_retries_total{job="alloy"}[5m])) or vector(0)) + sum(rate(loki_write_dropped_entries_total{job="alloy"}[5m]))`. No comparison, noData Alerting, so a vanished first term (alloy not scraped) is NoData and fires. The `or vector(0)` is on the retries term only, which is lazily created; the other two terms keep the NoData semantics. To be confirmed in the proof (healthy, 403, stopped, plus Loki unreachable if cheap).

## 6. Positions and storage
`loki.source.docker` has no positions argument; it keeps its offsets in the component data directory under `--storage.path`. Promtail's `/tmp/positions.yaml` was lost on container recreate. Decision: **no volume**; set `--storage.path=/var/lib/alloy/data` (inside the container, lost on recreate, same as today) so behaviour is unchanged, and no new durable state is introduced. Consequence recorded in the runbook: after Alloy is recreated it re-reads from the start of each retained container log, and Loki drops exact duplicates by timestamp+line. The proof run checks this (see test_plan).

## 7. Other findings
- `--disable-reporting` stops Alloy's usage telemetry to Grafana; set it.
- `loki.source.docker` already decodes the Docker json-file framing, so Promtail's `docker {}` stage has no Alloy counterpart.
- The Loki label guard test parses `scrape_configs` YAML; the Alloy config is not YAML, so the test must change (routed to testing-planner, draft only).
