# TCK-20260512-RPG-HISTORY-BOUNDS

## Title
RPG Strategic & Transaction History Bounding

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Enforce capacity limits on entity strategic history (leads, concerns, turning points) and transaction logs in the V2 Engine to mitigate state bloat and memory inflation in long-running simulations.

## Scope
- Implement `CapacityService` for collection trimming.
- Create `CapacityEnforcementPhase` pipeline phase.
- Implement rolling history buffers in `AuthoritativeState`.
- Support scoring-based trimming for strategic collections.

## Out of Scope
- Dynamic adjustment of capacity limits based on available system memory.

## Acceptance Criteria
- `processed_transaction_ids` capped at 1,000.
- `transaction_trace` capped at 100.
- Strategic collections (leads, concerns, etc.) capped based on `CognitionProfile`.
- Zero performance overhead when entities are within capacity bounds.

## Related Tickets
- TCK-20260512-PERF-HARDENING

## Related Docs
- `performance_implementation.md`

## Related Stored Artifacts
- `walkthrough.md`

## Related Code Areas
- `src/core/state.py`
- `src/engine/apply.py`
- `src/engine/pipeline_phases/capacity_enforcement.py`
- `src/strategy/capacity.py`

## Assumptions / Open Questions
- None

## Implementation Notes
- Used a size-based pre-check in `CapacityEnforcementPhase` to optimize performance for entities within bounds.
- Fixed a bug where `turning_points_add` was not being applied in `ApplyPath`.

## Test Summary
- `scratch/test_growth.py`: Verified stability of bounds over 1,500 ticks.
- `tests/perf/test_perf_strategic.py`: Verified performance targets.

## Files Changed
- `src/core/state.py`
- `src/core/updates.py`
- `src/core/strategic.py`
- `src/engine/apply.py`
- `src/engine/pipeline.py`
- `src/engine/pipeline_phases/capacity_enforcement.py`
- `src/strategy/capacity.py`
- `performance_implementation.md`

## Completion Summary
- Successfully implemented memory-safe history bounds.
- All collections are now strictly capped.
- Verified zero-overhead for entities within bounds.
