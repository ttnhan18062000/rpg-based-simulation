---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG
phase: done
date: 2026-08-07
tags: [observability, performance]
---

# TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG

## Title
`test_scale_performance_and_footprint` places all 100 entities at the same tile, triggering a
spurious `LAW-SPAWN-OCCUPANCY` violation and failing its own zero-telemetry-accumulation assertion

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/perf/test_observability_scale_validation.py::test_scale_performance_and_footprint`
constructs 100 entities via `V2EntityBuilder(idx).combat(hp=100, alive=True).location(10.0,
10.0).build()` for every `idx` — every entity is placed at the literal same coordinates. This
triggers a real `LAW-SPAWN-OCCUPANCY` `InvariantViolation` on kernel construction (entity 1 and
entity 2 both occupy tile (10, 10)), which then fails the test's own
`assert len(kernel._event_recorder.events) == 0` assertion (the violation event itself
accumulates). Confirmed pre-existing and unrelated to observability event-shaping work — the test
file's only commit predates this session by a long margin, and the failure is a deterministic
consequence of the test's own entity-placement code, not anything downstream.

Found incidentally while running the full `tests/perf/` suite during
`TCK-20260806-PUSH-CUTOVER-PHASE2` (Phase 2's cutover). Also observed:
`tests/perf/test_profiler_integrity.py::test_recorded_tick_compute_includes_all_phases` errors
when run immediately after this test in the same session (passes standalone) — likely a
test-isolation/ordering artifact of this same failure, not an independent second bug.

## Scope
Give each of the 100 test entities a distinct, non-colliding position (e.g. spread across a grid
or increment by tile size per entity) so the test measures scale/performance as intended, without
tripping a real hard-law violation as an unintended side effect.

## Out of Scope
- The `LAW-SPAWN-OCCUPANCY` hard-law check itself — working as designed, correctly catching a
  genuine placement collision; not the bug.

## Acceptance Criteria
- [x] `test_scale_performance_and_footprint` passes without triggering `LAW-SPAWN-OCCUPANCY`
- [x] `test_recorded_tick_compute_includes_all_phases` passes reliably in the full `tests/perf/`
      suite, not just standalone — confirmed by running it directly after the fixed scale
      validation test

## Related Tickets
- TCK-20260806-PUSH-CUTOVER-PHASE2 (found this incidentally)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/perf/test_observability_scale_validation.py`

## Assumptions / Open Questions
None.

## Implementation Notes
`HardLawMonitor._check_spawn_occupancy` (`src/observability/hard_law_monitor.py:163-164`) collides
on integer-truncated tile coordinates (`int(pos[0]), int(pos[1])`), not exact float equality —
confirmed by reading the actual check before picking a fix, rather than assuming a smaller spacing
would suffice. Spread the 100 entities across a 10x10 grid, each on its own integer tile
(`10.0 + (idx % 10)`, `10.0 + (idx // 10)`), guaranteeing zero collisions regardless of grid size.

## Test Summary
`tests/perf/test_observability_scale_validation.py`: 2 passed (was 1 failed). Confirmed the
`test_profiler_integrity.py::test_recorded_tick_compute_includes_all_phases` ordering artifact is
also resolved — passes when run directly after the fixed scale-validation test in the same
session (previously errored in this exact sequence). Full `tests/perf/ -m "not slow"`: 40 passed,
39 deselected — no other regressions.

## Files Changed
- `tests/perf/test_observability_scale_validation.py`

## Completion Summary
Fixed the entity-placement collision by spreading the 100 test entities across a 10x10 grid of
distinct integer tiles, matching `LAW-SPAWN-OCCUPANCY`'s actual collision granularity (traced
directly from `HardLawMonitor`, not assumed). Both the direct symptom (spurious hard-law
violation) and the secondary ordering artifact in `test_profiler_integrity.py` are resolved by
this one fix, confirming the ticket's own hypothesis that they shared a root cause.
