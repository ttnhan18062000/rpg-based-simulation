---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261015-LOKI-37-READINESS-VIA-PROMTAIL
phase: inprogress
date: 2026-10-15
tags: [platform, observability]
---

# TCK-20261015-LOKI-37-READINESS-VIA-PROMTAIL

## Title
Observability profile: take Loki 3.7.8 / Promtail 3.6.8 and probe Loki readiness from Promtail

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Dependabot #562 bumps `grafana/loki` 3.0.0 → 3.7.8 and `grafana/promtail` 3.0.0 → 3.6.8. platform-implementer's local
run at a455ca428 (2026-10-15) showed the loki 3.7.8 image has no `wget` and no `sh`, so the compose healthcheck
(`wget --spider .../ready`) can never pass. `/ready` itself answers `ready` after ~15 s. promtail and watchdog
`depends_on: loki: service_healthy`, so `--profile observability up` aborts. Promtail 3.6.8 is healthy with its
bash `/dev/tcp` check, and the Grafana Loki datasource works. Owner decision 2026-10-15: drop Loki's in-image
healthcheck and probe Loki from promtail, which has bash.

## Scope
- `compose.yaml`:
  - loki and promtail images: take #562's tag@digest pins (loki 3.7.8, promtail 3.6.8).
  - loki: remove the `healthcheck` block, with a comment saying why (no wget/sh in the image; readiness is probed from promtail).
  - promtail: `depends_on: loki: condition: service_started`. Its healthcheck requires both its own `localhost:9080/ready`
    and `loki:3100/ready` to answer HTTP 200, over bash `/dev/tcp`. Keep the timing settings, and add a `start_period`
    if Loki's ~15 s start needs it.
  - watchdog: replace `loki: service_healthy` with `promtail: service_healthy`, so watchdog still starts only after Loki
    is ready.
  - The header comment on line 6 (watchdog depends_on loki) stays accurate or is updated.
- PR body says it supersedes Dependabot #562; the user closes #562 after merge.

## Out of Scope
Promtail → Grafana Alloy migration (step-2 decision). Backend/ai_worker scrape jobs, Grafana password, port binding (step 2).
Any `src/**` change.

## Acceptance Criteria
- `docker compose --profile observability config -q` passes (validated in CI).
- **Running locally:** `--profile observability up -d` brings every service to `healthy`, or running for watchdog,
  which has no healthcheck. promtail stays unhealthy while loki is stopped and turns healthy again once loki is back.
  Grafana's Loki datasource health check passes, and a Loki query returns lines. Record what was run, as in
  TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13's Test Summary.
- Disk headroom checked with `tools/sessions/disk_headroom.py` before pulling; the stack is torn down afterwards.

## Related Tickets
TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13 (same profile, same evidence shape); TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 2: observability)

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13/`

## Related Code Areas
`compose.yaml`, `docker/promtail-config.yml` (read only)

## Assumptions / Open Questions
- Promtail retries pushes until Loki accepts them, so `service_started` loses no logs; the implementer confirms this
  in the local run.
- The e2e/test compose usage, if any, does not depend on loki being `service_healthy`. Grep for it before changing.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
