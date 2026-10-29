# Implementation Sequence — devops-step2-observability-local

Written by hand. One PR for the whole folder, from a `platform-implementer-local-*` branch. Host ubuntu (#618).

## Order

1. TCK-20261018-OBSERVABILITY-PROFILE-HARDENING  (no deps)
2. TCK-20261018-TEMPO-TRACE-BACKEND  (after 1: both edit `compose.yaml`; the config part and the synthetic-span proof need no rpg work)
3. TCK-20261018-SCRAPE-BACKEND-METRICS-PORT  (blocked on rpg R1: backend metrics port 9109 on main)
4. TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF  (needs 2 and 3, plus rpg R2 request histogram and R3 OTel middleware on main)

Epic: TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL (closes last).

## rpg prerequisites (issue #622, filed by lead-planner; rpg-planner owns src/**)

- R1: internal backend metrics port 9109 (`BACKEND_METRICS_PORT`, `expose` only). Option A, decided on #618.
- R2: HTTP request-duration histogram on the R1 registry, labelled method, route template and status class.
- R3: OTel ASGI middleware + redis client spans, 10 % head sampling (env), off when the OTLP endpoint is unset, and a
  test that `src/engine/**` imports no `opentelemetry`. The deps are runtime deps of the API (lead reviews pyproject/uv.lock).

## Why This Order Matters

1 and 2 both edit `compose.yaml`, so they run in sequence. 1 and 2 can be built and proven while R1-R3 are pending;
3 and 4 can't. If R1-R3 are late, the PR can still go up with 1 and 2 only, while 3 and 4 stay in this folder
(the owner decides at PR time).

Every stack run, image pull or build on this host is asked of lead-planner first, one at a time (host rules, 2026-10-18).

## Update 2026-10-19 (R1 #648 and R2 #654 on main)

- 1 and 2 are done (#627). 3 (SCRAPE-BACKEND-METRICS-PORT) runs now, in the batch `platform-implementer-local-slo-alerts`
  together with step-3's SLO alert, Redis cause alert and Redis drill (one PR). rpg's R1 did not touch compose, so the
  `expose: ["9109"]` hunk is ticket 3's.
- 4 (API-DASHBOARD-AND-TRACE-PROOF) still waits for R3 (OTel). It now follows step-3's
  TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK and copies its PromQL (the rule file is the single source; equality checked in
  ticket 4's test plan, no tests/**).

## Update 2026-10-27 (epic closed, ticket 4 split out)

1-3 are done (#627, #688). Ticket 4 (API-DASHBOARD-AND-TRACE-PROOF) moved to `agent-working/tickets/todos/devops-api-dashboard-trace/`,
BLOCKED on rpg R3, which has no ticket or date. This folder moves to done/ with the closed epic (owner choice, 2026-10-27).
