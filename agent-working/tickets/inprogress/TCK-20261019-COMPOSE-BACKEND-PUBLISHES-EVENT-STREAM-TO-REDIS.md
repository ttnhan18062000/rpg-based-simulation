---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261019-COMPOSE-BACKEND-PUBLISHES-EVENT-STREAM-TO-REDIS
phase: inprogress
date: 2026-10-19
tags: [platform, observability]
---

# TCK-20261019-COMPOSE-BACKEND-PUBLISHES-EVENT-STREAM-TO-REDIS

## Title
Default compose stack: the backend publishes the event stream to Redis, so ai_worker has work

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by platform-implementer (u24) during the Redis 8 soak for #646 (2026-10-19). `compose.yaml` sets neither
`SIM_STREAM_BACKEND` nor `SIM_REDIS_URL` on the backend service; it sets only `REDIS_URL`, which the stream producer
does not read. With nothing set, `ObservabilityConfig.get_stream_backend()` (`src/observability/config.py`) falls back
to the `local-dev` profile and returns `in_process`, and `get_redis_url()` defaults to `redis://localhost:6379/0`. So
`simulation:events` stays empty and ai_worker idles, because its own defaults are `redis` and `redis://redis:6379/0`.
The ai_worker lag/pending gauges and alert (#541 item 2) and the step-3 "stop Redis under load" drill (ubuntu, #618)
depend on the stream actually flowing. Announced on #618 (comment 6253821018).

## Scope
- `compose.yaml` backend `environment:`: add `SIM_STREAM_BACKEND=redis` and `SIM_REDIS_URL=redis://redis:6379/0`, with a
  one-line comment saying why (the producer reads `SIM_*`, not `REDIS_URL`; ai_worker consumes `simulation:events`).
- Replace the unused `REDIS_URL=redis://redis:6379/0` on **backend and ai_worker** with `SIM_REDIS_URL=redis://redis:6379/0`.
  rpg-planner confirmed on 2026-10-19, on the #646 tip, that nothing in `src/` reads plain `REDIS_URL`: the producer
  reads `SIM_*`/`RPG_*` (`src/observability/config.py:308,321`), and the anomaly worker reads `SIM_*`
  (`worker.py:417-419`). A variable nothing reads looks like configuration but does nothing, which is how this bug
  went unnoticed. Set `SIM_STREAM_BACKEND=redis` on ai_worker as well, explicitly, even though its default matches.
- Make sure the backend waits for redis `service_healthy` (add the dependency if it is missing). The adapter degrades
  without Redis, but at startup it should connect.

## Out of Scope
`SIM_DEPLOYMENT_PROFILE=production`, which also changes queue sizes and other defaults. Any `src/**` change: the
producer's defaults stay as they are. Observability-profile services and prometheus.yml are ubuntu's (step 2).

## Acceptance Criteria
- `docker compose config -q` passes (validated in CI).
- **Running locally:** after `docker compose up -d` (default profile) with a live sim, `XLEN simulation:events` grows,
  and `XINFO GROUPS simulation:events` shows ai_worker's group with lag and pending that don't grow over about 5 min.
  Backend readiness stays green, and there are no stream or adapter errors in the backend logs.
- Redis stopped for about 30 s under the live sim: the backend stays up (the adapter degrades), and the stream resumes
  after Redis restarts. Record what happened, including whether events were dropped.
- The change lands after #646 (Redis 8) or is rebased onto it.

## Related Tickets
TCK-20261018-DEPS-REDIS-8 (#646); TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS (rpg).

## Related Docs
`docs/guides/simulation_quality.md` (env table: SIM_STREAM_BACKEND, SIM_REDIS_URL);
`docs/plans/archive/observability_process_isolation.md` (stream producer)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`; `src/observability/config.py` (read only); `src/observability/anomaly/worker.py` (read only)

## Assumptions / Open Questions
- Publishing to Redis does not change simulation determinism: the stream is an observability side channel. If the
  implementer finds anything that reads the stream back into the engine, stop and report.
- Ubuntu may prefer to fold this into a step-2 branch; check #618 before starting.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
