---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Steps
1. `compose.yaml`: backend `expose: ["9109"]` (no `ports`).
2. `docker/prometheus.yml`: job `rpg-backend` -> `backend:9109`, with a comment that S4's TargetDown covers it.
3. Config checks: `compose config -q` (both profiles), `promtool check config` from the pinned image.
4. Live checks in the batch's single stack run (slot b): target up, `sim_current_tick` and
   `http_request_duration_seconds_bucket` return series; `curl localhost:8000/metrics` is 401; 9109 not reachable from
   the host.
5. List which `simulation.json` panels show data and which use metric names nobody exports (record only).

## Scope guards
No `src/**`. No host port for 9109. No edit to `simulation.json`.
