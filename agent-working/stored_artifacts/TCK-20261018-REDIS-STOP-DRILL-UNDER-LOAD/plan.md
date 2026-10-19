---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Steps
1. `tools/loadtest/drill_redis_stop.sh` (or a `run.py` subcommand) as scoped; UTC timestamps for every event; ntfy polled
   with a read token from the gitignored secrets, never printed.
2. Hypotheses written in the record before the run.
3. Slot (c), one heavy run asked of lead-planner: full profile, Locust at a steady step below the knee, stop Redis,
   fixed outage window, start Redis, tail, stop.
4. The record `docs/runbooks/records/<date>-drill-redis-stop.md` (blameless), runbook fixes in this PR.
5. Stack down without `-v`; `data/runs` ownership checked; only this run's data cleaned by run id.

## Scope guards
No `src/**` fixes (fyi to rpg-planner). One run, not repeated chaos.
