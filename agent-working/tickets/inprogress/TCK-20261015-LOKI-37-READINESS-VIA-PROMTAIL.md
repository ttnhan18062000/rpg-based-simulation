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
- `compose.yaml`: loki 3.7.8 and promtail 3.6.8 pinned by tag + digest (#562's pins); loki's healthcheck block removed with a comment; promtail `depends_on: loki: service_started`; promtail healthcheck is two `/dev/tcp` GET /ready probes (own :9080 and loki:3100, each in a subshell so fd 3 is reopened) with `start_period: 30s`; watchdog depends on `promtail: service_healthy` instead of loki; the line-6 header comment updated.
- No other compose or test file depends on loki being `service_healthy` (searched yaml/yml and tests).

## Test Summary
- **validated (static):** `docker compose --profile observability config -q` passes. CI result: to confirm on the PR.
- **running locally** (project `lokiprobe`, `--profile observability up -d --build watchdog grafana`, which starts redis, backend, prometheus, loki, promtail, grafana, watchdog; **frontend and ai_worker were not started** to save disk, since the loki change does not touch them): backend, prometheus, promtail, redis and grafana reached `healthy`; loki has no healthcheck and ran; watchdog ran. Grafana's `Loki` datasource health returned `Data source successfully connected`, and the `Prometheus` datasource health was OK.
- **Logs through Loki:** queries via Grafana's datasource proxy returned lines for the loki, promtail and backend containers (so promtail ships logs to Loki 3.7.8).
- **loki stopped -> promtail unhealthy:** after `docker stop` of loki, promtail went from healthy to `unhealthy` at about 40 s (5 failing probes at a 10 s interval). After `docker start` of loki, promtail was `healthy` again within 30 s.
- Loki 3.7.8 logged `empty ring` once at startup and `context canceled` querier lines when queries ended or loki was stopped; promtail logged only the `watchConfig` warning. The watchdog logged `Metrics HTTP 401`, the known `/metrics` scrape-auth issue (step 2), not this change.
- Idle memory (MiB): grafana 363, backend 140, loki 70, promtail 53, prometheus 29, watchdog 22, redis 5.
- Disk: root had 4.1 GB free before the run (`disk_headroom.py` did not finish in time, so `df` was used); the stack, volumes and pulled images were removed afterwards (5.7 GB free).

## Files Changed
- `compose.yaml`

## Completion Summary
Loki 3.7.8 and promtail 3.6.8 run in the observability profile. Loki has no healthcheck; promtail's healthcheck now requires both its own and Loki's /ready, and the watchdog waits on promtail. Supersedes Dependabot #562 (the user closes it after merge).
