---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-SCRAPE-BACKEND-METRICS-PORT

## Title
Prometheus: scrape the backend's internal metrics port 9109 instead of the admission-gated /metrics on 8000

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Carry-in 1 on #618. `docker/prometheus.yml` scrapes `backend:8000/metrics`, which returns 401 because it sits behind
`require_admission` (`src/api/server.py`). So nothing from the backend reaches Prometheus today, and the existing
"RPG Simulation" dashboard is empty. Option A was decided on #618: rpg serves metrics on an internal-only port 9109
(`BACKEND_METRICS_PORT`, compose `expose` only). That is R1 in the epic, and its compose hunk comes in rpg's PR, which
platform-planner reviews. This ticket switches the scrape job and proves the target is up.

## Scope
- `docker/prometheus.yml`: job `rpg-backend` targets `backend:9109`. Remove the 8000 target; don't keep a job that
  always fails.
- Review rpg's R1 compose hunk (`expose: ["9109"]`, the env var, no host port) as platform-planner. The implementer
  doesn't duplicate it.
- A Prometheus rule file is **not** added here (alerts are step 3).
- Check the existing `docker/grafana/dashboards/simulation.json`: list which panels now show data and which still use
  metric names the collector doesn't export (for example "Redis & Kafka Latency Distribution"). Record the list only;
  fixing or pruning that dashboard is a separate decision.

## Out of Scope
- The port itself, the admission change and the R2 histogram (rpg).
- The ai_worker job `ai_worker:9108` (step 3, blocked on rpg-next).

## Acceptance Criteria
- In the Prometheus targets page, `rpg-backend` is `up` (**running locally**), and `sim_current_tick` returns a
  series in a query.
- `curl -s -o /dev/null -w '%{http_code}' localhost:8000/metrics` still returns 401: the public port stays gated.
  9109 is not reachable from the host.
- `docker compose --profile observability config -q` passes.
- The panel list for `simulation.json` is in the Test Summary.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL`. **Blocked on rpg R1** (backend metrics port 9109, issue #622) reaching main.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D1)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/prometheus.yml`, `compose.yaml` (rpg's hunk, reviewed here), `src/api/server.py` (read only)

## Assumptions / Open Questions
- R1 is requested from rpg-planner in issue #622 (filed by lead-planner, 2026-10-18).

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
