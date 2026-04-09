# TCK-20260327-WINDBIGMOD

## Title
Wind Pillar Finalization & Core Models Refactor (BIGMOD)

## Description
This ticket combines the maintenance refactor of overgrown modules with the functional finalization of the "Wind Pillar" (Vector Flow Fields). It ensures the AI navigation system is both clean (Clean Code) and highly performant (Architecture).

## Scope
- **BIGMOD**: 
    - Extract `StatsShim` and delegation logic from `src/core/models.py` into `src/core/stats_proxy.py`.
    - Reduce `models.py` complexity by splitting entity-specific logic into companion modules.
- **Wind Pillar**:
    - Finalize `FlowField.get_vector` with robust bilinear smoothing.
    - Wire `FlowFieldManager` into `NavigationHandler` and `TownHandler` for high-traffic targets.
    - Implement caching logic for static vs dynamic targets.

## Acceptance Criteria
- [ ] No single `.py` file in `src/core/` exceeds 600 lines.
- [ ] `StatsShim` is successfully extracted and fully tested in its own module.
- [ ] Flow Fields provide valid, smoothed direction vectors for Towns as verified by tests.
- [ ] AI navigation switches to Flow Fields for targets > 10 tiles away when a field is available.
- [ ] 100% test pass for `tests/unit/ai/test_flow_fields.py` and `tests/unit/core/test_models.py`.
- [ ] Performance profile shows > 20% CPU reduction during mass-movement scenarios.

## Related Tickets
- TCK-20260322-RPG_REFINEMENT (InProgress)
- TCK-20260326-BIGMOD (Subsumed)
- epic-09-improved-pathfinding-and-movement.md
