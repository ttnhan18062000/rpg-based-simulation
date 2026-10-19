---
status: active
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
