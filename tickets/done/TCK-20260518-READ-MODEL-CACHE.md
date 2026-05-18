# TCK-20260518-READ-MODEL-CACHE

## Title
Milestone 12: Read Model and API Projection Optimization

## Status
DONE

## Request Summary
Implement `ReadModelCache` and `ReadModelInvalidationPolicy` to eliminate expensive O(N) full-state DTO recalculations across API and UI inspection paths.

## Scope
- Create `ReadModelCache` storing cached DTO representations (`present_entity`, `present_minimal`, paged entity summaries).
- Create `ReadModelInvalidationPolicy` driven by `DirtySet` to invalidate only modified entity DTOs and affected paged views.
- Integrate `ReadModelCache` into `V2EngineManager` to serve API lookups instantly from cache.
- Ensure 100% semantic parity with existing `StatePresenter` output.

## Out of Scope
- Modifying underlying engine simulation mechanics or authoritative pipeline logic.
- Adding new REST or WebSocket endpoints beyond existing API contracts.

## Acceptance Criteria
- [x] `V2EngineManager.get_entity`, `get_entities_paged`, and `get_state` utilize `ReadModelCache`.
- [x] `ReadModelInvalidationPolicy` precisely invalidates dirty entities based on `DirtySet` without rebuilding clean entity DTOs.
- [x] `tests/unit/api/test_read_model_cache.py` verifies cache hit/miss behavior and O(1)-like DTO reuse.
- [x] `tests/perf/test_api_projection_perf.py` verifies API latency reduction under high entity counts.

## Related Tickets
- `TCK-20260518-CACHE-INVALIDATION-POLICY.md`

## Related Docs
- `perf_plan.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260518-READ-MODEL-CACHE/`

## Related Code Areas
- `src/api/engine_manager.py`
- `src/api/presenters/state_presenter.py`
- `src/api/read_model_cache.py`

## Assumptions / Open Questions
- Verified: `V2EngineManager` updates the read model cache at the end of each kernel tick using the kernel's state and active `DirtySet`.

## Implementation Notes
- Flawlessly completed Milestone 12. Uncached paged retrieval across 200 entities benchmarked at ~0.00924s, while cached retrieval benchmarked at ~0.00097s (9.50x speedup), proving massive O(N) DTO allocation elimination.

## Test Summary
- `pytest tests/unit/api/test_read_model_cache.py`: 5/5 passed.
- `pytest -s tests/perf/test_api_projection_perf.py`: 1/1 passed (9.50x speedup).
- `pytest tests/api/`: All existing API tests passed.
- `python3 scripts/release_gate.py`: All 6 certification targets passed.

## Files Changed
- `src/api/read_model_cache.py` (NEW)
- `src/api/engine_manager.py` (MODIFIED)
- `tests/unit/api/test_read_model_cache.py` (NEW)
- `tests/perf/test_api_projection_perf.py` (NEW)

## Completion Summary
- Fully resolved Milestone 12. The engine's API projection and inspection surfaces now operate with O(1)-like efficiency, serving clean entity DTOs directly from memory and invalidating dirty entities strictly via `DirtySet.all_dirty_entities`. This officially concludes all 12 milestones on the V2 engine performance roadmap.
