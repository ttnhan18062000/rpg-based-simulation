---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Steps
1. Wait for rpg's 0.3 bucket on main (#622); confirm `le="0.3"` exists in the live histogram before the fire test.
2. `docker/grafana/provisioning/alerting/rules-slo.yaml`: group `slo`, two rules (latency p95 > 0.3 on 2xx excluding
   /health and unmatched; 5xx ratio > 1%), `runbook_url`, `summary` with single-`$` labels (S4 lesson), routed through
   S4's policy to ntfy. noData/execErr choices stated.
3. `docs/runbooks/api-latency-slo.md` + README row. State the 429-inside-4xx limit and D5's availability SLO without an
   alert.
4. Slot (b), one heavy run asked of lead-planner: full profile; age soak to the page cap (#627 method); Locust steps
   recording server-side p50/p95/p99 next to client-side; a step above the knee for the fire test; record pending,
   firing, ntfy received, load stop, resolved.
5. Measurement section in the runbook or a record under `docs/runbooks/records/`.

## Scope guards
No threshold edit for the test. No `tests/**`. No Alertmanager. Single-`$` in annotations.

## Update (implementer, 2026-10-19)
- Preflight added to slots (b) and (c) after the first (b) attempt stopped at the live checks: the local `platform-backend` image (2026-10-18 03:02) predated R1/R2 and had no `src/api/http_metrics.py`, so `rpg-backend:9109` was refused and `le="0.3"` was absent. Before anything else: `docker image inspect platform-backend --format '{{.Created}}'` must be after the build, and `docker compose exec backend python -c "import src.api.http_metrics"` must succeed. A `docker compose build backend ai_worker` (alone, `COMPOSE_PARALLEL_LIMIT=1`) is slot (b0).
