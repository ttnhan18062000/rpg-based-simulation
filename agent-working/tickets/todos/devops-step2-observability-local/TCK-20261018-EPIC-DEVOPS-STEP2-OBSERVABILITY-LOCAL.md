---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL

## Title
DevOps step 2 (host ubuntu): one API dashboard (metrics and logs) and one API request trace in Tempo, running locally

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Step 2 of `docs/architecture/devops_plan_amendment_proposal.md`, moved to host ubuntu by the owner on 2026-10-16 (#618)
and briefed by lead-planner on 2026-10-18: one API dashboard plus one OTel + Tempo request trace at the API layer. The
engine imports no tracing code (ADR D4). Everything is proven on the local compose stack first. Carry-ins come from the
u24 platform-planner's comment on #618 (Grafana default password, ports bound on all interfaces, Promtail socket, the
backend `/metrics` 401).

## Scope
Four platform child tickets, in the order in `SEQUENCE.md`:

1. `TCK-20261018-OBSERVABILITY-PROFILE-HARDENING`: Grafana admin password from a compose secret (no `admin`
   default), host ports bound to `127.0.0.1`, Promtail's `docker.sock` read-only with the risk recorded.
2. `TCK-20261018-TEMPO-TRACE-BACKEND`: Grafana Tempo in the `observability` profile, plus the Tempo datasource with
   trace-to-logs and trace-to-metrics links.
3. `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT`: Prometheus scrapes rpg's internal backend metrics port `backend:9109`
   instead of the admission-gated `backend:8000/metrics` (401 today).
4. `TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF`: the API dashboard (rate, errors, p50/p95/p99 by route, backend logs,
   trace links) and the end-to-end local proof.

**rpg-side prerequisites** (src/**, rpg-planner's; requested through lead-planner, not filed here):
- **R1** internal backend metrics port 9109 (`BACKEND_METRICS_PORT`, compose `expose` only): option A, already decided on #618.
- **R2** HTTP request metrics on that registry: a request-duration histogram labelled by method, route **template**
  (not the raw path) and status class. There are no request metrics today; the collector only exports `sim_*` engine gauges.
- **R3** OTel middleware in `src/api/` (ADR D4): FastAPI/ASGI server spans and redis client spans, head sampling
  10 % by default (env-configurable), off when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, and a test that nothing under
  `src/engine/` imports `opentelemetry`. Its `opentelemetry-*` packages are runtime deps of the API image (lead
  reviews the `pyproject.toml`/`uv.lock` diff).

## Out of Scope
- Any edit under `src/**` (R1-R3 are rpg's).
- The ai_worker scrape job and lag alert (step 3 folder, blocked on rpg's ai_worker `/metrics` reaching main).
- Migrating Promtail to Grafana Alloy (a follow-up; see child 1).
- Step 1 follow-ups (#614) and the gitleaks/Semgrep lane: u24 platform's.
- Steps 4-6.

## Acceptance Criteria
- All four children DONE, in one PR from a `platform-implementer-local-*` branch.
- Evidence uses only the D7 labels: "running locally" for the stack, the dashboard and the trace; "validated" for
  config checks. Nothing is called "deployed".
- No file under `src/engine/` imports tracing code (R3's test proves it; this epic checks the test exists and passes).
- The observability profile still fits the host: the measured peak `docker stats` table, Tempo included, is recorded.

## Related Tickets
- Step 1: `TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY` (#561).
- Step 3: `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`.
- rpg: `TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS` (on rpg branches, not on main yet).
- Issues #618 (host split and carry-ins), #541 (accepted inputs), #614 (u24 step-1 follow-ups).

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 2), `docs/architecture/devops_baseline_adr.md` (D1, D4, D7)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/prometheus.yml`, `docker/tempo.yaml` (new), `docker/grafana/**`, `.gitignore`

## Assumptions / Open Questions
- Children 3 and 4 can't finish until R1 and R2 are on main; child 2's trace proof needs R3. Children 1 and 2
  (config part) can land first.
- Host ubuntu: 6 vCPU, about 9 GB RAM, roughly 3 GB available while the fleet runs. Compose stacks and image pulls
  run one at a time, after asking lead-planner, under the host rules in the 2026-10-18 brief.

## Implementation Notes
Epic tier: the children carry the implementation.

## Test Summary
See the child tickets.

## Files Changed
See the child tickets.

## Completion Summary
(open)
