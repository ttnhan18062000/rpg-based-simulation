# Implementation Sequence — devops-step2-observability-local

Written by hand. One PR for the whole folder, from a `platform-implementer-local-*` branch. Host ubuntu (#618).

## Order

1. TCK-20261018-OBSERVABILITY-PROFILE-HARDENING  (no deps)
2. TCK-20261018-TEMPO-TRACE-BACKEND  (after 1: both edit `compose.yaml`; the config part and the synthetic-span proof need no rpg work)
3. TCK-20261018-SCRAPE-BACKEND-METRICS-PORT  (blocked on rpg R1: backend metrics port 9109 on main)
4. TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF  (needs 2 and 3, plus rpg R2 request histogram and R3 OTel middleware on main)

Epic: TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL (closes last).

## rpg prerequisites (requested through lead-planner; rpg-planner owns src/**)

- R1: internal backend metrics port 9109 (`BACKEND_METRICS_PORT`, `expose` only). Option A, decided on #618.
- R2: HTTP request-duration histogram on the R1 registry, labelled method, route template and status class.
- R3: OTel ASGI middleware + redis client spans, 10 % head sampling (env), off when the OTLP endpoint is unset, and a
  test that `src/engine/**` imports no `opentelemetry`. The deps are runtime deps of the API (lead reviews pyproject/uv.lock).

## Why This Order Matters

1 and 2 both edit `compose.yaml`, so they run in sequence. 1 and 2 can be built and proven while R1-R3 are pending;
3 and 4 can't. If R1-R3 are late, the PR can still go up with 1 and 2 only, while 3 and 4 stay in this folder
(the owner decides at PR time).

Every stack run, image pull or build on this host is asked of lead-planner first, one at a time (host rules, 2026-10-18).
