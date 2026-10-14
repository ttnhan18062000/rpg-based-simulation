---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13
phase: inprogress
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13

## Title
Upgrade the observability profile to Prometheus v3 and Grafana 13 before step 2 builds dashboards on them

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The owner chose to take these majors now (no game impact; observability profile only). This supersedes Dependabot #563 (prometheus v2.50.0 → v3) and #564 (grafana 10.3.3 → 13).

## Scope
- `compose.yaml`: `prom/prometheus` and `grafana/grafana` move to the current v3.x and 13.x exact tags, digest-pinned in
  the existing comment style.
- Prometheus v3 migration check against `docker/prometheus.yml` and the compose `command:` flags. Known v3 changes to
  verify: removed or renamed feature flags, the UI, scrape protocol/content-type negotiation, and the `/-/healthy`
  endpoint used by the healthcheck.
- Grafana 13 check: datasource and dashboard provisioning (`docker/grafana/provisioning/**`), whether
  `docker/grafana/dashboards/simulation.json` still loads (Angular panels were removed in 12), the `/api/health` healthcheck,
  and the `GF_SECURITY_ADMIN_PASSWORD` env name.
- Fix whatever breaks in `docker/**`, in this ticket.

## Out of Scope
Loki/Promtail versions (minor group); replacing Promtail (deprecated in favour of Grafana Alloy), which is a step 2 decision. The Grafana password and port-binding hardening also move to step 2.

## Acceptance Criteria
- `docker compose --profile observability up -d`: all services reach healthy (running locally).
- Prometheus targets page shows `rpg-backend` UP; the Grafana datasource test passes; `simulation.json` renders with no panel-plugin errors (screenshot or API output in Test Summary).
- `compose config -q` passes; publish-images CI stays green.

## Related Tickets
Dependabot #563, #564; `TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS`.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1, step 2)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/prometheus.yml`, `docker/grafana/**`

## Assumptions / Open Questions
Run `tools/sessions/disk_headroom.py` before pulling the new images.

## Implementation Notes
`compose.yaml`: `prom/prometheus:v3.15.0` and `grafana/grafana:13.2.4`, both exact tag + digest (confirmed with imagetools). Prometheus v3 needed no change to `docker/prometheus.yml` or its flags. Grafana 13 needed two changes: `mem_limit` 256m -> 768m (it hit 256m and restarted once; first start peaked at 480 MiB, settled at 317 MiB), and `healthcheck.start_period: 120s` (first start with the 10.x data volume ran a long migration, about 2 to 3 minutes on a heavily loaded host). `simulation.json` uses only timeseries, stat, gauge, heatmap, logs and row panels, so no Angular panels.
## Test Summary
- **running locally** (`docker compose --profile observability up -d --build`): prometheus, loki, promtail, redis, backend, frontend and grafana reached `healthy` (grafana after the fix above). Grafana version 13.2.4 `database: ok`.
- Grafana datasources `Prometheus` and `Loki`: `/api/datasources/uid/<uid>/health` returned `OK` for both. Dashboard `RPG Simulation: Analytics & Diagnostics` (uid `sim-v2`) is provisioned.
- Prometheus v3 logged no warnings or errors.
- **Finding, not caused by this change:** the `rpg-backend` target is DOWN with `HTTP 401` because the backend's `/metrics` requires an API key (`dependencies=[Depends(require_admission)]`, since #61) and `docker/prometheus.yml` has never sent credentials. The ticket's `rpg-backend UP` criterion therefore cannot pass on any Prometheus version until someone decides how Prometheus authenticates (an rpg/`src/api` decision); reported to platform-planner.
- Grafana logs also show harmless errors: missing `provisioning/plugins` and `provisioning/alerting` directories, and TLS failures reaching grafana.com (plugin catalogue).
- Idle memory peaks after this change: grafana 480 MiB (start), backend 357, loki 93, prometheus 40, promtail 42, ai_worker 33, watchdog 22, frontend 6, redis 8.
- CI build of images and publish-images on the PR: to confirm.
## Files Changed
- `compose.yaml`
## Completion Summary
Prometheus v3.15.0 and Grafana 13.2.4 run cleanly in the observability profile; the `/metrics` 401 is a pre-existing separate issue.
