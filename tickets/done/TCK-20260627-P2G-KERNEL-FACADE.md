---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2G-KERNEL-FACADE
phase: done
date: 2026-06-27
tags: [p2, coupling, kernel, hard-law-monitor, worldindexservice, facade, refactor]
---

# TCK-20260627-P2G-KERNEL-FACADE

## Title
Route `hard_law_monitor` spatial queries through `Kernel` instead of direct `WorldIndexService` import

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P2

## Request Summary
`src/observability/hard_law_monitor.py:10` imports `WorldIndexService` directly. All other observability files (`sweeper`, `controller`, `harness`) only import `Kernel`. This couples `hard_law_monitor` to a concrete engine internal — a `WorldIndexService` interface change breaks the monitor without a visible dependency signal. Source: D14 F3, Risk 8/15.

## Scope
- Add a spatial query delegation method to `Kernel` (e.g., `kernel.get_entities_in_region(region_id)` or `kernel.spatial_query(...)`) or expose `WorldIndexService` access through a `KernelQueryFacade`.
- Update `hard_law_monitor.py` to call the `Kernel` method instead of importing `WorldIndexService` directly.
- Remove the direct `WorldIndexService` import from `hard_law_monitor.py`.

## Out of Scope
- Refactoring other monitoring files.
- Changing `WorldIndexService` itself.

## Acceptance Criteria
- [ ] `hard_law_monitor.py` no longer imports `WorldIndexService` directly.
- [ ] Spatial queries in `hard_law_monitor` go through `Kernel` (via a new method or existing delegation).
- [ ] All existing hard law monitor tests pass.
- [ ] `grep "WorldIndexService" src/observability/hard_law_monitor.py` returns no results.

## Related Tickets
- TCK-20260627-P2H-TIMELINE-APPEND (similar coupling cleanup — can be done in same sprint)

## Related Docs
- `docs/audits/D14_coupling_depth.md` F3
- `docs/observability/hard_law_monitor.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260519-SIM-OBS-HARD-LAW/`

## Related Code Areas
- `src/observability/hard_law_monitor.py:10` (import to remove)
- `src/engine/kernel.py` (add delegation method)
- `src/engine/world_index.py` (source of `WorldIndexService`)

## Assumptions / Open Questions
- The spatial query in `hard_law_monitor` is likely `get_entities_near()` or similar — check the exact usage before designing the facade.
- `Kernel` already exposes `RuntimeStatus` and other query surfaces; adding one spatial query method is low-risk.

## Implementation Notes
- Added `Kernel.get_world_indexes(state, dirty)` as a `@staticmethod` on `Kernel` (src/engine/kernel.py, end of class). Delegates to `WorldIndexService.get_indexes()` via a lazy local import — no circular import introduced.
- Removed `from src.engine.world_index import WorldIndexService` from `hard_law_monitor.py:10`; replaced with `from src.engine.kernel import Kernel`.
- Changed the single call site in `check_occupancy()` from `WorldIndexService.get_indexes(state, dirty_set)` to `Kernel.get_world_indexes(state, dirty_set)`.
- No behavior change; pure import-boundary refactor. All callers of `HardLawMonitor.check()` are unaffected.

## Test Summary
- Regression: `pytest tests/ -k hard_law -m "not slow"`.
- Verify: `grep "WorldIndexService" src/observability/hard_law_monitor.py` is empty.

## Files Changed
- `src/observability/hard_law_monitor.py`
- `src/engine/kernel.py`

## Completion Summary
Added `Kernel.get_world_indexes(state, dirty)` static method to `src/engine/kernel.py` as a thin facade delegating to `WorldIndexService.get_indexes()` via a lazy local import. Updated `src/observability/hard_law_monitor.py` to import `Kernel` instead of `WorldIndexService`, and replaced the single `WorldIndexService.get_indexes()` call with `Kernel.get_world_indexes()`. No behavior change — pure import-boundary refactor. D14 F3 (Risk 8/15) is resolved: `hard_law_monitor` now aligns with `sweeper`, `controller`, and `harness` in depending only on the `Kernel` boundary. All 5 hard-law monitor tests and 16 architecture lane tests pass.
