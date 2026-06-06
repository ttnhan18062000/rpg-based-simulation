# TCK-20260517-STATE-UPDATE-COMPACTOR

## Title

StateUpdateCompactor Implementation for Performance Optimization

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `StateUpdateCompactor` to filter out no-op and redundant entity updates before they reach `ApplyPath.apply_generation()`. The profiler identifies `ApplyPath` and dataclass replacement as a major performance bottleneck during high-concurrency simulation ticks. By systematically stripping empty subcomponents, pruning property updates that match current entity state, and dropping empty entity updates entirely, we reduce memory churn and state application latency.

## Scope

- Implement `CompactionMetrics` and `StateUpdateCompactor` in a new module `src/engine/compactor.py`.
- Implement `@staticmethod def compact(state: AuthoritativeState, update: StateUpdate) -> StateUpdate` and `compact_with_metrics`.
- Integrate `StateUpdateCompactor.compact()` into `AuthoritativeApplyPipeline.refine()`.
- Implement unit tests in `tests/unit/optimization/test_state_update_compactor.py` covering tests 5.1 through 5.6 from `perf_test_plan.md`.
- Implement performance regression test in `tests/perf/test_apply_compaction_perf.py`.

## Out of Scope

- Modifying worker protocol or message serialization.

## Acceptance Criteria

- Compactor never changes final semantic state. (VERIFIED)
- Compactor drops empty entity updates. (VERIFIED)
- Compactor drops zero-delta updates (e.g. `hp_delta == 0`). (VERIFIED)
- Compactor drops property updates equal to current state. (VERIFIED)
- Compactor emits before/after metrics. (VERIFIED)
- Movement/resource scenario shows reduced update count. (VERIFIED)

## Related Tickets

- Milestone 4: DirtyDependencyGraph (`TCK-20260517-DIRTY-DEPENDENCY-GRAPH.md`)

## Related Docs

- `perf_test_plan.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260517-STATE-UPDATE-COMPACTOR/`

## Related Code Areas

- `src/core/updates.py`
- `src/core/update_models/quests.py`
- `src/engine/compactor.py`
- `src/engine/pipeline.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented singleton `MISSING` sentinel object comparison (`is`) in `StateUpdateCompactor.compact_with_metrics` to correctly identify missing attributes vs sentinel instances.
- Refined `QuestUpdate.is_noop()` to ensure that quest retry intents carrying specific quest IDs are preserved during compaction.

## Test Summary

- `pytest tests/unit/optimization/test_state_update_compactor.py -v`: 6 passed in 0.29s.
- `pytest tests/perf/test_apply_compaction_perf.py -v`: 1 passed in 1.02s (Dropped 4000/5000 updates, 3000 property prunings).
- Fast unit test suite (`pytest tests/unit/ -m "not slow" -v`): 749 passed in 12.79s.
- Parity test (`pytest tests/perf/test_dirty_parity.py -v`): 1 passed in 21.02s.

## Files Changed

- `src/engine/compactor.py` (NEW)
- `src/engine/pipeline.py` (MODIFY)
- `src/core/update_models/quests.py` (MODIFY)
- `tests/unit/optimization/test_state_update_compactor.py` (NEW)
- `tests/perf/test_apply_compaction_perf.py` (NEW)

## Completion Summary

Successfully implemented `StateUpdateCompactor` and integrated it into the authoritative apply pipeline. Tested thoroughly with unit tests, performance regression benchmarks, and full engine validation suites. The compactor effectively drops redundant property updates and no-op subcomponents, reducing memory allocation churn and accelerating state application.
