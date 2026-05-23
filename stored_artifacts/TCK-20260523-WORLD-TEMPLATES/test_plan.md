# Test Plan: World Template and Recipe System

We will write unit tests to cover all required cases and invariants defined in `world_phase11.md`.

## Unit Tests Path

`tests/unit/worldbuilding/test_world_recipes.py`

## Test Cases

1.  **Population Recipe Expansion**:
    *   Verify that `PopulationRecipeSpec` with `count: 100` converts to correct `PopulationSpec` count in the expanded spec.
    *   Verify that custom profiles (`stats_profile`, `inventory_profile`) are preserved or correctly mapped.

2.  **Resource Recipe Expansion**:
    *   Verify that `ResourceRecipeSpec` with `count: 15` generates exactly 15 `ResourceNodeSpec` elements in the expanded list.
    *   Verify resource IDs are stable and traceable (e.g. `res_wood_forest_0` to `res_wood_forest_14`).

3.  **Building Recipe Expansion**:
    *   Verify that `BuildingRecipeSpec` with `count: 3` generates exactly 3 `BuildingSpec` elements.
    *   Verify building IDs are stable and traceable.

4.  **Seeding & Determinism**:
    *   Verify that running the expander multiple times with the same template and seed produces identical `WorldSpec` objects.

5.  **Topology and Containment Guards**:
    *   Verify that if a region recipe's bounds exceed the topology dimensions, the expander rejects it immediately with a validation or containment exception.

6.  **No Bypassing Validation**:
    *   Verify that the expanded `WorldSpec` successfully passes through `WorldValidator.validate(spec, strict=True)`.
    *   Verify that if a recipe refers to a nonexistent spawn region or faction, the expanded spec fails the standard `WorldValidator` pass (demonstrating validation is not bypassed).
