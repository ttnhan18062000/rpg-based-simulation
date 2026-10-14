---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS
phase: open
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS

## Title
Compose: make the observability stack an optional profile, add memory limits, and make the health checks real

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
DevOps step 1, T1 (rebuilt here; the parked `devops-s1` version is not used). Today `docker compose up` starts all
9 services, none of them has a memory limit, and the backend health check passes even on an HTTP 500. Step 4's
`kind` cluster also depends on these memory limits being in place.

## Scope
- **Profile `observability`:** prometheus, grafana, loki, promtail **and watchdog**. watchdog has `depends_on`
  loki and prometheus and polls Loki, so it cannot stay in the default set. Default `docker compose up` = backend,
  redis, ai_worker, frontend.
- **Memory limits on every service** (`mem_limit`, or `deploy.resources.limits.memory`, used consistently). Start
  from these values: backend 1g, ai_worker 512m, redis 256m, frontend 64m, prometheus 512m, grafana 256m, loki 512m,
  promtail 128m, watchdog 256m. Then set each final value to its observed peak in `docker stats` plus headroom,
  and record the table in this ticket's Test Summary.
- **Health checks:**
  - backend: replace the `requests.get(...)` check, which never fails on a non-2xx response, with one that exits
    non-zero on any failure (for example `urllib.request.urlopen`, which raises on >=400).
  - Add checks for frontend (`wget --spider http://localhost/`), grafana (`/api/health`) and promtail (`:9080/ready`).
  - ai_worker and watchdog have no HTTP port today: leave them without a check and say why in a compose comment.
  - `depends_on` uses `condition: service_healthy` wherever the target has a check.
- grafana admin password from `${GRAFANA_ADMIN_PASSWORD:-admin}` instead of a literal.
- A short "profiles" note at the top of `compose.yaml`.

## Out of Scope
- Base-image pinning and `npm ci` (child 4).
- The ai_worker metrics port and its health check (rpg's `TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS`).
- Removing promtail's `docker.sock` mount. It is a known risk and is noted for step 2.
- Any change under `src/**`.

## Acceptance Criteria
- `docker compose config -q` and `docker compose --profile observability config -q` both succeed.
- Default `docker compose up -d` starts exactly backend, redis, ai_worker and frontend, and those with checks reach
  `healthy` (**running locally**).
- With `--profile observability` all 9 services start, and the ones with checks reach `healthy`.
- The backend check fails when `/health` returns a non-2xx response or the backend is down: shown once by pointing it
  at a bad path or stopping uvicorn.
- Every service has a memory limit, and the measured peak table is in the Test Summary.

## Related Tickets
Epic `TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY`.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1, step 4's mem_limit dependency)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/**`

## Assumptions / Open Questions
- Run `python3 tools/sessions/disk_headroom.py` before building locally (about 4.6 GB free). If there isn't enough room
  for the observability profile's images, record "validated (config only)" for that profile instead of "running locally".

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
