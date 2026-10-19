---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT
phase: inprogress
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-SCRAPE-BACKEND-METRICS-PORT

## Title
Prometheus: scrape the backend's internal metrics port 9109 instead of the admission-gated /metrics on 8000

## Status
INPROGRESS

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
- `docker/prometheus.yml`: add job `rpg-backend` targeting `backend:9109`. (The always-401 `backend:8000` job was
  already removed by S4's `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`, amended 2026-10-18; S4's `TargetDown`
  rule then covers this job too.)
- (amended 2026-10-19) rpg's R1 (#648) did not touch `compose.yaml`, so the compose hunk is this ticket's: the backend gets
  `expose: ["9109"]` (never `ports`). `BACKEND_METRICS_PORT` is left at its code default 9109 unless setting it explicitly
  makes the file clearer; `BACKEND_METRICS_HOST` stays at its default (all interfaces inside the container).
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
- `docker/prometheus.yml`: job `rpg-backend` -> `backend:9109` added (its comment says the old 8000 job was removed by S4 because that route is admission-gated). No rule file here.
- `compose.yaml`: the backend gets `expose: ["9109"]` (never `ports`); `BACKEND_METRICS_PORT` and `BACKEND_METRICS_HOST` are left at their code defaults (9109, every interface inside the container; `src/api/metrics_port.py`). rpg's R1 did not touch compose, so this hunk is this ticket's.
- The 0.3 s bucket the SLO alert needs is NOT on main yet (`src/api/http_metrics.py` `_BUCKETS` has 0.25 and 0.5); that gates the SLO fire test, not this ticket.

## Test Summary
- **validated:** `docker compose config -q` for both profiles; the rendered backend service has `expose: ['9109']` and the only published port is `8000:8000`; `promtool check config` from the pinned image (SUCCESS, with the `rpg-backend` job).
- **running locally** (2026-10-19, second attempt; the first stopped because the local backend image predated R1; images rebuilt 16:32:14Z; record `docs/runbooks/records/2026-10-19-api-slo-alert-fire-test.md`): the `rpg-backend` target is `up`; `sim_current_tick` returns a series (851 at the first check); `count by (le) (..._bucket{le="0.3"})` is 1; `GET :8000/metrics` returns 401; `:9109` from the host is unreachable (HTTP code 000).
- **`simulation.json` panels** (instant queries one minute after a fresh start; a young world): with data: World Age, Difficulty Mult, Active Entities, TPS, Calamity Status, Global Gold Circulation, Blacksmith & Shop Volume, Raw Events, Technical Errors (`sim_errors_total`). No series: Faction Populations, Entity Level Distribution, Total Combat Casualties, Detailed Phase Profiling, Redis & Kafka Latency Distribution, Worker Health and the invalid-actions query (the two Loki panels were not evaluated). Recorded for the dashboard ticket; no dashboard edit.
- Evidence files: `agent-working/stored_artifacts/TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK/run-2026-10-19/live_checks_2.txt`, `dashboard_panels.txt`.

## Files Changed
(open)

## Completion Summary
(open)
