# TCK-20260326-BIGMOD

## Title
Refactor Overgrown Modules (>1000 lines)

## Description
Several core modules have exceeded the 1000-line threshold, leading to high cognitive load and potential maintainability issues. This ticket aims to break these modules down into smaller, logically separated files following the Single Responsibility Principle (SRP) and "Clean Code" standards.

## Scope
- `src/ai/states.py` (1428 lines):
    - Separate state handlers into logical groups (e.g., `src/ai/states/combat.py`, `src/ai/states/social.py`, `src/ai/states/navigation.py`).
    - Use `src/ai/states/__init__.py` to maintain backward compatibility of the `STATE_HANDLERS` registry.
- `src/core/models.py` (1286 lines):
    - Extract `StatsShim` and related proxy logic into `src/core/stats_proxy.py`.
    - Separate `Entity` subtypes or complex aggregation methods into companion modules if possible.
    - Ensure `Stats` and `Entity` base classes remain clean.

## Acceptance Criteria
- [ ] No single `.py` file exceeds 800 lines.
- [ ] Public APIs/Imports remain unchanged for dependent modules.
- [ ] `STATE_HANDLERS` registry in `src/ai/states` is correctly populated from sub-modules.
- [ ] 100% of existing unit and integration tests pass after refactoring.
- [ ] `StatsShim` delegation logic is verified to avoid recursion.

## Related Tickets
- TCK-20260325-RPG_DEPTH (Done) - Introduced complexity in `models.py`.
- TCK-20260322-RPG_REFINEMENT (In Progress) - Depends on AI State stability.
