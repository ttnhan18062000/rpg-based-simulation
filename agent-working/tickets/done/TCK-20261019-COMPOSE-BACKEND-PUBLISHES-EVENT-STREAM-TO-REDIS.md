---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261019-COMPOSE-BACKEND-PUBLISHES-EVENT-STREAM-TO-REDIS
phase: done
date: 2026-10-19
tags: [platform, observability]
---

# TCK-20261019-COMPOSE-BACKEND-PUBLISHES-EVENT-STREAM-TO-REDIS

## Title
Default compose stack: the backend publishes the event stream to Redis, so ai_worker has work

## Status
DONE

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
- #618 advance notice: platform-planner's comment of 2026-10-18T18:56Z covers exactly this backend `environment:` edit; no objection from ubuntu before the edit.
- Backend `environment:` now sets `SIM_STREAM_BACKEND=redis` and `SIM_REDIS_URL=redis://redis:6379/0`, with a comment that the producer reads `SIM_*`, not `REDIS_URL`.
- ai_worker: the unused `REDIS_URL` is replaced by the same two `SIM_*` variables (explicit; its defaults already matched).
- The backend and ai_worker already had `depends_on: redis: service_healthy`, so nothing was added.
- `src/**` untouched. Nothing was found that reads the stream back into the engine.

## Test Summary
Checked in an isolated compose project built from the branch (`git archive` of the tip plus this compose.yaml), default services only (backend, redis, ai_worker), own volume, no override file, a live simulation running:
- `docker compose config -q` passes and shows the two `SIM_*` variables on both services.
- **Steady state, 6 samples over 5 min:** XLEN 132, 165, 198, 232, 282, 324 (grows, about 33 per min). The consumer group `observatory:consumers` had lag 0 and pending 0 at every sample (entries-read equal to XLEN). Backend health 200, 0 restarts on any service.
- **Redis stopped 30 s:** the backend stayed up (health 200, `Up ... (healthy)`) and ai_worker stayed up (0 restarts). The backend logged 1 ERROR (`RedisStreamAdapter failed to publish event`) and 23 WARNING lines (`Redis offline or unreachable ... running in degraded mode`). ai_worker logged 7 connect errors and 1 `Connection closed by server` while Redis was away. All of them were name-resolution failures during the outage.
- **After Redis restarted:** the stream resumed and the group had lag 0 and pending 0 at every sample over the next 2 min (XLEN 377 to 426, entries-read equal to XLEN). Events published during the outage were dropped: about 53 entries arrived in the 110 s window around the outage, where the steady rate predicts about 60. This is an estimate, not an exact count, since the adapter has no drop counter.
- Not run: the whole pytest suite (YAML-only change; CI runs the static checks).

## Files Changed
`compose.yaml` (backend and ai_worker `environment:`); this ticket.

## Completion Summary
The default compose stack now publishes the simulation event stream to Redis, so ai_worker has work and the lag and pending checks (#541 item 2, #618 step 3) have a flowing stream to observe. Verified in an isolated stack: XLEN grows, lag and pending stay 0, and a 30 s Redis outage leaves both services up with the stream resuming (a few events dropped during the outage, approximately 7 by estimate).
