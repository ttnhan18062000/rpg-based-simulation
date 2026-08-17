---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL
phase: done
date: 2026-08-17
tags: [engine, bug, testing]
---

# TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL

## Title
Fix a real spawn-placement collision in `V2EngineManager._build()` plus a test-isolation leak
that turned it into a hard CI failure

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on the "API / tools / logging" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/observability/test_metrics_export.py::test_metrics_endpoint_direct[asyncio]` and
`::test_multiple_registries_prevent_collision` both raised
`HardLawViolationError: [ERROR] LAW-SPAWN-OCCUPANCY on entity 1: Initial placement collision on
tile (64, 64): entity 1 and entity 6 both occupy this space.`

Investigation found two independent, compounding bugs:

1. **Real production bug**: `src/api/engine_manager.py::V2EngineManager._build()` places the hero
   at fixed `(64.0, 64.0)` and monsters along a diagonal `(60.0 + i, 60.0 + i)`. With the default
   `entities_count=10` (both this class's own default and `src/api/server.py`'s real startup call
   site), `i=4` lands exactly on the hero's tile. Not test-fixture-only scope — reachable from the
   real server bootstrap path.
2. **Test-isolation leak**: `tests/engine/test_hard_law_monitor.py::test_observability_modes_and_kernel_integration`
   sets `ObservabilityConfig`'s class-level global override mode to `DEBUG` and never reset it.
   Whether the collision check raises or just warns depends on this mode (default `LIGHT` =
   warn-only); the leaked `DEBUG` override from `tests/engine` (collected before
   `tests/observability` in the same CI job) turned a silent warning into a hard failure.

## Scope
- `src/api/engine_manager.py::V2EngineManager._build()`: skip any diagonal monster-placement
  offset whose integer-truncated tile collides with the hero's tile, matching
  `LAW-SPAWN-OCCUPANCY`'s own collision granularity (per the
  `TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG` precedent), continuing the diagonal
  afterward. General for any `entities_count`.
- `tests/engine/test_hard_law_monitor.py::test_observability_modes_and_kernel_integration`: reset
  `ObservabilityConfig`'s override on exit via `request.addfinalizer(ObservabilityConfig.clear_all_overrides)`.

## Out of Scope
- `_run_initial_placement_check`/`HardLawMonitor.check_initial_placement` — confirmed correctly
  implemented and correctly, newly catching a real, pre-existing bug; not touched.
- Any Mechanics Bible/parity ledger entry — none references this spawn pattern (verified via
  grep); none needs updating.
- Any other ticket in this batch.

## Acceptance Criteria
- [x] `V2EngineManager` with the default `entities_count=10` no longer triggers
      `LAW-SPAWN-OCCUPANCY` on construction.
- [x] `tests/engine/test_hard_law_monitor.py tests/observability/test_metrics_export.py` (the
      exact combined scope that reproduced the CI failure) passes.
- [x] The real CI job's full invocation (`pytest tests/api tests/cli tests/tools tests/logging
      tests/engine tests/observability -m "not slow"`) shows no failures attributable to this bug.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None — no Mechanics Bible/parity ledger entry references this spawn pattern.

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL/`

## Related Code Areas
- `src/api/engine_manager.py`
- `tests/engine/test_hard_law_monitor.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Rewrote `V2EngineManager._build()`'s monster-placement loop to skip any diagonal offset landing
on the hero's tile (int-truncated comparison, matching the hard-law check's own granularity),
continuing the diagonal afterward so entity count and visual pattern are otherwise unchanged.
Added `request.addfinalizer(ObservabilityConfig.clear_all_overrides)` to the leaking test,
using the dedicated reset classmethod `ObservabilityConfig` already provides for exactly this
purpose. Both fixes were required together — fix 1 alone leaves the isolation leak able to
resurface via any other order-dependent interaction; fix 2 alone leaves a real, reachable
production bug live, merely silent again.

## Test Summary
- `pytest tests/engine/test_hard_law_monitor.py tests/observability/test_metrics_export.py -q`:
  17 passed (was reproducing the CI failure before the fix).
- `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
  slow" -q` (the real, full CI job invocation): 4 failed at that checkpoint, none attributable to
  this bug (`test_metrics_export.py` fully clean) — the remaining 4 (websocket/ws_protocol tests)
  were separate, independently investigated and fixed issues.

## Files Changed
- `src/api/engine_manager.py`
- `tests/engine/test_hard_law_monitor.py`

## Completion Summary
Fixed a real, reachable production bug (deterministic spawn-placement collision at the class's own
default `entities_count`) and a compounding test-isolation leak that turned it into a hard CI
failure rather than a silent warning. Both root causes confirmed via direct reproduction before
and after the fix, not assumed.
