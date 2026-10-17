---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-TEMPO-TRACE-BACKEND
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-TEMPO-TRACE-BACKEND

## Title
Compose: Grafana Tempo in the observability profile as the OTLP trace backend, with a Grafana datasource linking traces to logs and metrics

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ADR D4 sends API spans over OTLP to a local Grafana Tempo in the `observability` profile, with a `mem_limit`. The span
producer is rpg's middleware (R3 in the epic). This ticket provides the receiving end and the Grafana wiring, so a
trace can be opened from a log line or a dashboard panel.

## Scope
- **`tempo` service:** `profiles: ["observability"]`, an image pinned by version and multi-arch digest (like the other
  third-party images; Dependabot's docker-compose ecosystem then bumps it), a `mem_limit` (start at 512m, set from
  the measured peak), and a named volume for its data.
  - OTLP receivers on gRPC 4317 and HTTP 4318, `expose`d only (no host port).
  - The query port 3200 is internal only too; Grafana reaches it over the compose network.
- **`docker/tempo.yaml`:** single-binary, local filesystem storage, short block retention (for example 24h), no
  metrics-generator. Span metrics would be skewed by the 10 % head sampling; request rate and latency come from R2.
- **Healthcheck:** use `/ready` if the image has a probe tool. If it doesn't (as with Loki), say so in a compose
  comment and probe it from another container, the same way promtail probes Loki. Don't add a probe sidecar just for this.
- **Grafana datasource** (`docker/grafana/provisioning/datasources/datasource.yml`): a Tempo datasource, `uid: tempo`.
  - Trace to logs: Loki, filtered on the backend container and the trace id.
  - Trace to metrics: Prometheus.
  - The Loki datasource gets a `derivedFields` entry that turns a `trace_id` in a log line into a Tempo link. Find the
    real log field name in R3's output; don't guess it.
- **Backend env in compose:** `OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT:-}`, empty by default, so
  tracing stays off unless set. Also `OTEL_SERVICE_NAME=rpg-backend`, plus the sampling variable R3 defines (use its
  name).
  - D4 says off when unset, and the default profile has no Tempo. The observability `make` target or a documented
    `.env` line sets `http://tempo:4318` (or `:4317`, matching R3's exporter).
- Add the service to the profiles comment at the top of `compose.yaml`.

## Out of Scope
- The middleware, the exporter and the `opentelemetry-*` deps (rpg's R3).
- Tempo metrics-generator, service graphs, exemplar storage.
- Any host port for Tempo.

## Acceptance Criteria
- Both profiles' `docker compose config -q` pass. In the default profile no Tempo runs and the backend starts with an
  empty OTLP endpoint (**validated**).
- With `--profile observability` Tempo is up (healthy, or probed as documented), and Grafana's Tempo datasource
  "Test" succeeds (**running locally**).
- **Before R3 lands:** one synthetic span sent to Tempo (for example with `otel-cli` or `telemetrygen` in a throwaway
  container on the compose network, not installed on the host) is found by trace id in Grafana Explore.
- **After R3 lands:** the trace proof is in `TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF`.
- Tempo's measured peak memory is added to the `docker stats` table, and the whole observability profile still fits
  the host's available memory.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL`. After `TCK-20261018-OBSERVABILITY-PROFILE-HARDENING`
(both edit `compose.yaml`).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D1, D4)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/tempo.yaml` (new), `docker/grafana/provisioning/datasources/datasource.yml`

## Assumptions / Open Questions
- Tempo's exact version is chosen at implementation time: the latest stable release that is at least two weeks old.
  Record it and its digest in the ticket.
- Image pull and stack start: ask lead-planner first (host rules).

## Implementation Notes
- Tempo `grafana/tempo:3.0.3@sha256:0296560ac66f8a3600d7fb3014a52c189d4d9c3549ad6ff441bf2409855d68d5` (latest stable at least 2 weeks old on 2026-10-18: 3.0.3 is 2026-08-13, 3.0.4 is 2026-10-16). Digest from a registry query; image NOT pulled yet.
- `docker/tempo.yaml`: monolithic, local storage (`/var/tempo/{wal,blocks}`), `block_retention: 24h`, OTLP gRPC 4317 + HTTP 4318, query 3200. Written from Tempo "next" docs; Config corrected at runtime (see Test Summary).
- Service `tempo`: observability profile, `expose` only, `mem_limit: 512m` (start value), `tempo_data` volume, no healthcheck (no probe tool assumed; verify at runtime).
- Grafana datasource `tempo` (tracesToLogsV2 to Loki on `container=~".*backend.*"` + trace id, tracesToMetrics to Prometheus).
- Backend env: `OTEL_EXPORTER_OTLP_ENDPOINT=${...:-}` (empty), `OTEL_SERVICE_NAME=rpg-backend`.
- DEFERRED to R3 (#622): the Loki `derivedFields` entry (log field name unknown), the sampling variable, and the exporter port 4317 vs 4318.

## Test Summary
- PASS: `compose config -q` for default and observability profiles; YAML parse of tempo.yaml and datasource.yml.
- Runtime, 2026-10-18, local:
  - FIX 1: Tempo 3.0.3 rejected the `compactor:` block: `failed parsing config: ... yaml: unmarshal errors: line 14: field compactor not found in type app.Config` (restart loop). Retention moved to `backend_worker.compaction.block_retention` (found with `-help`: `-backend-worker.compaction.block-retention`); Tempo then started ("Tempo started", OTLP gRPC 4317 and HTTP 4318).
  - No volume permission problem: the WAL started on the fresh named volume without a `user:` or init service (no "permission denied" in the log).
  - Tempo is not on a host port. `GET http://tempo:3200/ready` from the grafana container returns `ready`. The image has no healthcheck (none added).
  - Grafana datasource test (`GET /api/datasources/uid/tempo/health`): `Data source is working`, status OK.
  - Synthetic span (OTLP/HTTP JSON POST to `tempo:4318/v1/traces`, sent with python from the backend container, so nothing was pulled or installed; no telemetrygen): trace id `580bb4a0b429886696ebeda847e80411`, found via Grafana's datasource proxy (`/api/datasources/proxy/uid/tempo/api/traces/<id>`) on the first try, span `synthetic-span`. This is the Grafana API, not the Explore UI.
  - Warnings, harmless: "metrics-generator is not configured", "unowned file entry ignored during wal replay file=blocks", a BackendScheduler "no jobs found".
  - Memory (`docker stats --no-stream`, max of 3 samples, idle apart from the synthetic span): tempo 35 MiB of 512m; whole profile peak sum about 710 MiB (backend 188, grafana 281, loki 74, tempo 35, watchdog 23, ai_worker 33, prometheus 30, promtail 18, proxy 13, redis 9, frontend 6). Host: available memory stayed >= 4.9 GB while up. A lower `mem_limit` for tempo is possible; left at 512m until a load run.
  - NOT done: Explore-UI check, trace to logs/metrics links (need rpg's R3 spans and log field), derivedFields.

## Files Changed
`compose.yaml`, `docker/tempo.yaml`, `docker/grafana/provisioning/datasources/datasource.yml`, this ticket.

## Completion Summary
(open)
