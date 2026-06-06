# TCK-20260404-STABILIZATION: Final AOA AI and Freezing Stabilization

## Description
Resolve AI decision errors and Pydantic validation failures occurring during snapshot freezing. This is the final cleanup following the AOA architectural pivot.

## Scope
1.  **AI State Regressions**:
    *   Fix `UnboundLocalError: Perception` in `navigation.py`.
    *   Fix `NameError: HeroClass` in `base.py`.
    *   Fix `AttributeError: Perception.get_faction_registry` in `combat.py`.
2.  **Core Model Freezing**:
    *   Update `SimulationModel.freeze()` to handle slotted and already-frozen models (like `Vector2`).
    *   Ensure recursive freezing uses `object.__setattr__` safely to bypass Pydantic's frozen model checks.

## Acceptance Criteria
- [x] `tests/e2e/test_combat_arena_e2e.py` passes 100%.
- [x] `tests/integration/api/test_api_payload.py` passes 100%.
- [x] No "AI: Decision error" logged in simulation output.
- [x] Full 700+ test suite passes without `ValidationError` related to frozen instances.

## Related Tickets
- TCK-20260402-VALIDATION
- TCK-20260330-CORE-STABILIZATION

## Status
DONE

**Tier:** standard
**Type:** chore
**Priority:** P1
