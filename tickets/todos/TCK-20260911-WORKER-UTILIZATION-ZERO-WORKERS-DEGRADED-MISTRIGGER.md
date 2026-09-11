---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER
phase: open
date: 2026-09-11
tags: [determinism, architecture]
---

# TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER

## Title
`WorkerManager.get_stats()`'s `worker_utilization=1.0` sentinel for `max_workers<=0` forces the
governor into `RuntimeMode.DEGRADED` unconditionally, regardless of actual compute pressure

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split out of `TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION` on 2026-09-11
(that ticket's own hotfix-tier disposition: confirmed real mis-trigger, real fix not trivial, filed
here per its own AC4). Root cause traced and confirmed via direct code reading, not assumed:

`WorkerManager.get_stats()` (`src/engine/worker_manager.py:229-232`):
```python
worker_utilization = (
    peak_active / self._max_workers
    if self._max_workers > 0 else 1.0
)
```
When `max_workers <= 0` (a real, intentional "workers disabled / synchronous execution" mode — not
an edge case), `worker_utilization` is **unconditionally forced to `1.0`** (100% "utilized"),
regardless of `peak_active` (which is always `0` in this mode, since there are no workers to be
active). `ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py:83-91`) reads this at its
very first evaluation:
```python
if signals.worker_utilization >= 0.9 or signals.queue_utilization >= 0.9:
    return RuntimeMode.DEGRADED
```
`worker_utilization=1.0` trivially satisfies `>= 0.9` on every single tick, from tick 1, regardless
of real load — there is no organic-pressure story here, `peak_active` is always `0`, `_max_workers`
is `0`, the 100% figure is a pure sentinel artifact of the division guard, misread by the governor
as genuine saturation.

**Confirmed general, not specific to any one caller** — 3 real production call sites construct a
`RuntimeProfile` with `max_worker_count=0`:
- `src/engine/scenario_runtime.py:395` (`ScenarioRuntimeService._build_kernel()` — every Campaign
  episode and any other `ScenarioRuntimeService` consumer)
- `src/engine/scenario_checkpoint.py:94` (`ScenarioCheckpointer`, an unrelated subsystem)
- `src/config/loader.py:74` — `BROKER_DISABLED=1` env var **explicitly, intentionally** forces
  `max_worker_count=0` as a documented, real operational mode (logged: `"BROKER_DISABLED=1
  detected. Forcing max_worker_count=0."`) — this is not an internal implementation detail of one
  service, it is a real, user-facing configuration path.

**Re-observed directly (2026-09-11), superseding the origin ticket's "empty world" framing**: this
was first found via an empty-world `campaign_life_arc` probe, but re-run with the now-real 16-entity
world (post `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`): `DEGRADED`/`EXACT_DIRTY` still
fires at tick 1, identically. The entity count was never the cause — confirms this is the real,
general governor mis-trigger, not an artifact of the empty-world reproduction.

## Scope
- Decide the correct semantic for `worker_utilization` when `max_workers <= 0`: most likely `0.0`
  (workers are deliberately disabled — there is no worker-based pressure signal to report at all,
  the metric is inapplicable rather than maximal), but confirm this doesn't silently mask a real
  signal the governor needs from some other path when running in worker-disabled mode — check
  whether any other pressure signal (`tick_compute_ms`, `work_debt_total`, `queue_utilization`)
  already covers real compute pressure independently in this mode, so `worker_utilization` isn't
  the *only* thing standing between `NORMAL` and a real overload going undetected.
- Fix `WorkerManager.get_stats()`'s sentinel value (or, if the real fix belongs at the governor's
  own evaluation layer instead — e.g. `ResourceGovernor._get_indicated_mode()` should skip the
  `worker_utilization` check entirely when `profile.max_worker_count <= 0` rather than relying on
  `WorkerManager`'s own sentinel value being governor-aware — decide which layer owns this
  correctly during Investigate, don't assume the origin ticket's own guess).
- Confirm the fix doesn't regress the real worker-based degradation this mechanism exists to catch
  for the normal (`max_workers > 0`) case — that logic must stay correct and untouched.
- Real test coverage: a fresh kernel with `max_worker_count=0` must start in (or promptly settle
  into) `RuntimeMode.NORMAL` absent real compute pressure, confirmed via a real, uninstrumented
  multi-tick run — not merely asserting the sentinel value changed.
- Check all 3 real call sites above are still correctly governed after the fix (a `BROKER_DISABLED`
  real-config-mode run, a `ScenarioCheckpointer` run, and a `ScenarioRuntimeService` run).

## Out of Scope
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s own scope (what happens once
  `EXACT_DIRTY` is entered, for any reason) — unaffected by this ticket either way; fixing this
  mis-trigger reduces how OFTEN that ticket's starvation pattern can occur but does not eliminate
  the underlying starvation mechanism itself if `DEGRADED` is ever entered for a real reason.
- The Kernel wall-clock mid-tick throttle's own general determinism disposition — a separate,
  already-deferred issue (user said let it sit); this ticket's mis-trigger is independent of that
  one (this fires even in `audit_mode`-style zero-compute conditions, not from wall-clock timing).
- Any change to `RuntimeMode`/`GovernorPolicy`'s own escalation/recovery/dwell-time logic beyond the
  one `worker_utilization` input this ticket targets.

## Acceptance Criteria
- [ ] A real, uninstrumented run with `max_worker_count=0` (matching `ScenarioRuntimeService`'s own
      real construction) starts in `RuntimeMode.NORMAL` and stays there absent real compute
      pressure — confirmed via a real multi-tick test, not a unit test of the sentinel value alone.
- [ ] The fix is scoped to the correct layer (`WorkerManager` sentinel vs. `ResourceGovernor`'s own
      evaluation logic) with rationale for the choice recorded.
- [ ] Normal (`max_workers > 0`) worker-pressure-driven `DEGRADED` escalation is confirmed
      unregressed by a real test.
- [ ] All 3 real `max_worker_count=0` call sites (`ScenarioRuntimeService`, `ScenarioCheckpointer`,
      `BROKER_DISABLED=1`) are confirmed correctly governed after the fix.

## Related Tickets
- `TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION` (origin; closed with this
  ticket filed as its own real-fix follow-up, per that ticket's own AC4)
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` (the downstream consequence once
  `DEGRADED`/`EXACT_DIRTY` is entered, for any reason — reducing false-positive `DEGRADED` entry
  here reduces, but does not eliminate, that ticket's own starvation exposure)

## Related Docs
- `docs/architecture/simulation_watchdog.md` (adaptive governor design intent)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
- `src/engine/worker_manager.py` (`WorkerManager.get_stats()`, the `worker_utilization=1.0`
  sentinel, lines 229-232)
- `src/engine/governor.py` (`ResourceGovernor._get_indicated_mode()`, the `>= 0.9` check reading it)
- `src/engine/scenario_runtime.py`, `src/engine/scenario_checkpoint.py`, `src/config/loader.py`
  (the 3 real `max_worker_count=0` call sites)

## Assumptions / Open Questions
- Whether the correct fix layer is `WorkerManager`'s own sentinel or `ResourceGovernor`'s own
  evaluation logic is not decided here — real Investigate/Plan work for whoever picks this up.
- Whether any other real caller anywhere in the codebase relies on the current `1.0`-when-disabled
  behavior (intentionally or by accident) is not yet checked beyond the 3 call sites already found
  constructing `RuntimeProfile(max_worker_count=0)` directly — a broader grep for any code branching
  on `worker_utilization` specifically (not just the governor) should be part of Investigate.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
