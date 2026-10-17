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
OPEN

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
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
