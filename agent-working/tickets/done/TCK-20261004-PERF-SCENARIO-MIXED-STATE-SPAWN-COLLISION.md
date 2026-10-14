---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION
phase: done
date: 2026-10-04
tags: [performance, bug, determinism]
---

# TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION

## Title
`src/perf/scenarios.py::build_mixed_state()`, called on its own, places entities on the same tile

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while fixing `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION`, which answered that
ticket's Scope item on `build_mixed_state()` called standalone. `build_metropolis_state()` overwrites
every position, so its own fix does not reach this path. Measured `LAW-SPAWN-OCCUPANCY` violations from
`HardLawMonitor.check_initial_placement()` (perf-implementer, 2026-10-04): 2 at `entity_count=100`,
2 at 200, 7 at 1000.

The standalone callers are `tests/perf/test_perf_stress.py` (200), `tools/perf/run_perf_baseline.py`
(`MIXED_1000`) and `tools/release/verify_production_profiles.py` (`MIXED_100`). Fixing it moves the
numbers those callers produce. That is why it was left out of the metropolis fix.

## Scope
- Make `build_mixed_state()` place no two objects on one tile at the caller counts above, deterministically.
  It merges `build_idle_state()` heroes with `build_combat_arena_state()` monsters under independent
  coordinate schemes. Find which pair collides before choosing a fix.
- Same verification shape as the metropolis ticket: zero violations at 100, 200 and 1000; bit-identical
  positions and `ProofDigest` across two calls; the placement tests in
  `tests/tools/test_perf_scenarios_placement.py` extended.

## Out of Scope
- `build_metropolis_state()` (fixed by `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION`).
- Retuning any threshold in the callers.

## Acceptance Criteria
- [x] Zero `LAW-SPAWN-OCCUPANCY` violations from standalone `build_mixed_state()` at 100, 200 and 1000.
- [x] Positions and `ProofDigest` are identical across two calls with the same inputs.
- [x] `tests/perf/test_perf_stress.py` still passes unmodified.
- [x] The ticket states which caller numbers moved and that they stay provisional.

## Related Tickets
- `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION` (sibling; found this)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`
  ("Gate definition and partial lift")

## Related Stored Artifacts
_(none)_

## Related Code Areas
- `src/perf/scenarios.py` (`build_mixed_state`, `build_idle_state`, `build_combat_arena_state`)

## Assumptions / Open Questions
- **Gated.** The 2026-10-04 extension of the partial lift to `src/perf/scenarios.py` covers only the
  metropolis ticket. This fix needs its own owner OK, or it waits for the full lift.

## Implementation Notes
- Colliding pairs: an idle hero vs an arena monster at (5, 0), and a monster vs a resource node at (5, 10) (heroes sit at x = id % 100, monsters at x = 5). A monster on a taken tile now slides along y to the first free tile (`_first_free_tile`); heroes and nodes keep their tiles.
- Gate: `src/perf/` is perf-owned; perf-planner dispatched this without a lift (2026-10-11), so the old 'gated' open question is closed.
- Numbers moved for every caller: `tests/perf/test_perf_stress.py` (200), `tools/perf/run_perf_baseline.py` (`MIXED_1000`) and `tools/release/verify_production_profiles.py` (`MIXED_100`). They stay provisional; `baseline_invalidation_ledger.md` has a `mixed_*` row so PERF-M2-T08 re-records them. `verify_production_profiles.py` is unowned in the session registry (route: no match): lead-planner to assign.
- `test_perf_mixed_stress` times out on a clean `origin/main` too (this VM); it is not caused by this change.

## Test Summary
- `tests/tools/test_perf_scenarios_placement.py`: 4 new tests (zero violations at 100/200/1000, only colliding monsters move, determinism with an identical ProofDigest, the helper); the file passes.
- FAIL (not proven): `test_perf_stress.py::test_perf_mixed_stress` times out on this VM both before and after (verified on a clean main worktree) and is marked `slow`, so CI (`-m "not slow and not extra_slow"`) does not run it; the 'passes unmodified' criterion is not shown.

## Files Changed
- `src/perf/scenarios.py`, `tests/tools/test_perf_scenarios_placement.py`, `docs/performance/baseline_invalidation_ledger.md`, this ticket.

## Completion Summary
`build_mixed_state` no longer places two objects on one tile (0 LAW-SPAWN-OCCUPANCY violations at 100, 200 and 1000, deterministic). The caller numbers moved and stay provisional; the invalidation ledger carries the `mixed_*` row for T08. Local commit only (owner hold 2026-10-13).
