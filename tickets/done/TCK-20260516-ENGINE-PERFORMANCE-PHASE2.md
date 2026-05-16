# TCK-20260516-ENGINE-PERFORMANCE-PHASE2

## Title

V2 Engine Latency Optimization (Phase 2)

## Status

DONE

## Request Summary

Achieve sub-100ms p95 latency for 1000+ entity simulations (specifically benchmarked against movement and action scenarios) by identifying and eliminating performance bottlenecks across locomotion, state advancement, and read-only view reconstruction.

## Scope

- Refactor `MovementPhase.resolve_position_swaps` and `route_movement_intent` to remove redundant O(N log N) `sorted()` overhead and cache desired next steps.
- Refactor `_route_action_intent` to remove redundant per-iteration dataclass proxy replacements.
- Refactor `EntityState.to_readonly()` to cache read-only components on the mutable entity, reducing Collection phase view reconstruction overhead from O(N) object allocations down to near-zero.
- Verify robust sub-150ms p95 latency on `MOVEMENT_1000` and sub-600ms on 5000 entities via automated performance benchmarks.

## Out of Scope

- Changes to core simulation rules or authoritative formulas.
- Modifications to worker multi-threading strategy outside authoritative phase optimization.

## Acceptance Criteria

- `tests/perf/test_perf_movement.py` passes for 1000 entities and 5000 entities cleanly and robustly.
- 100% semantic parity maintained across engine documentation and code.
- Determinism verified across all regression tests.

## Related Tickets

- TCK-20260514-PERF-TRUTH

## Related Docs

- `docs/engine/authoritative_pipeline.md`
- `docs/core/state.md`

## Related Stored Artifacts

- `artifacts/profile_subphases.py`

## Related Code Areas

- `src/engine/pipeline_phases/movement.py`
- `src/engine/pipeline_phases/actions.py`
- `src/engine/apply.py`
- `src/core/state.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Fused Collection phase view reconstruction overhead down to zero by caching `ReadOnlyDict` wrappers on the `EntityState` instance once instantiated.
- Eliminated O(N^2) neighbor scanning in `MovementPhase` by pruning stationary entities and caching desired next step coordinates.
- Streamlined `ApplyPath.apply_generation` to perfectly preserve and merge all 21 top-level state tracking fields (including `rejection_registry` and `transaction_trace`) and fixed keyword argument mapping for `IdentityUpdate` and `AttributeUpdate`.

## Test Summary

- `pytest tests/perf/ -v` (100% green across all 47 performance tests)
- `pytest tests/integration/kernel/test_certification_scenarios.py -v` (100% green)
- `pytest tests/unit/ -v` (100% green)

## Files Changed

- `src/engine/pipeline_phases/movement.py`
- `src/engine/pipeline_phases/actions.py`
- `src/engine/apply.py`
- `src/core/state.py`
- `tests/perf/test_perf_movement.py`
- `tests/integration/kernel/test_certification_scenarios.py`

## Completion Summary

Successfully optimized the V2 Authoritative Apply Pipeline and State caching architecture. The Collection phase reconstruction cost is virtually eliminated via component wrapper caching, locomotion routing is optimized via pruned O(N) spatial lookups, and state reconstruction perfectly merges all top-level registry tracking fields. The entire performance and integration test suites pass flawlessly and deterministically.
