---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13
phase: open
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13

## Title
Upgrade the observability profile to Prometheus v3 and Grafana 13 before step 2 builds dashboards on them

## Status
OPEN

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
## Test Summary
## Files Changed
## Completion Summary
