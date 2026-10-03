---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-STRATEGIC-TESTS
phase: done
date: 2026-06-24
tags: [strategic, progression, test-setup, service-registry, item-registry]
---

# TCK-20260624-FIX-STRATEGIC-TESTS

## Title
Fix 3 strategic/progression tests with missing test fixtures and setup

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Three tests fail due to missing test environment setup, not logic bugs:

1. `test_service_opportunities_basic` — `ServiceOpportunityProvider.get_opportunities()` returns `[]` because `ServiceRegistry` is empty in the test environment. The test expects a `buy_item` opportunity for a hero in `hometown` but no fixture populates the registry with a service at `region_id='hometown'`.

2. `test_interaction_interrupted_by_damage` — the test asserts that an interaction is NOT reset when there's no damage. However, the entity's `interaction.target_node_id` is `None` (default), and `InteractionSystem.enforce()` also resets on "no valid interaction target", not just on damage. The test entity needs `target_node_id` set to trigger only the damage-interrupt code path.

3. `test_equipment_stat_injection_move_cost` — formula and implementation exactly match `docs/mechanics/01_entity_anatomy.md §2` (Move_Cost = max(5.0, 10.0 + weight/5.0 - agility×0.1)): no-equip → 9.5, iron_plate → 11.9. The failure is because `ItemRegistry.get('iron_plate')` returns `None` in the test scope — `ItemRegistry` is not initialized before the test runs, so equipment weight is never loaded and move cost stays at 9.5 for both cases.

## Scope
- `test_service_opportunities_basic`: add a fixture that registers a service with `region_id='hometown'` and `supported_affordances=['buy']` into `ServiceRegistry` before the test runs; teardown the registry after
- `test_interaction_interrupted_by_damage`: add `entity.interaction.target_node_id = 100` (or any valid node ID) to the test entity setup
- `test_equipment_stat_injection_move_cost`: add `ItemRegistry` initialization (or a minimal stub for `iron_plate` with `weight=12.0`) before the test

## Out of Scope
- Changing `ServiceOpportunityProvider`, `InteractionSystem`, or `EquipmentComponent` logic
- Changing the move cost formula

## Acceptance Criteria
- All 3 tests pass
- No regression in other strategic/progression tests

## Related Tickets
None

## Related Docs
- `docs/mechanics/01_entity_anatomy.md §2` — move cost formula (verified correct)
- `docs/mechanics/04_strategic_cognition.md` — service opportunities and interaction interrupts

## Related Code Areas
- `tests/unit/strategic/test_opportunities.py::test_service_opportunities_basic`
- `tests/unit/strategic/test_strategic_hardening.py::test_interaction_interrupted_by_damage`
- `tests/unit/progression/test_rpg_advancement.py::test_equipment_stat_injection_move_cost`
- `src/world/providers/services.py` — `ServiceOpportunityProvider.get_opportunities()`
- `src/engine/interaction.py:61–103` — `InteractionSystem.enforce()`
- `src/progression/leveling.py:116–154` — equipment stat injection

## Assumptions / Open Questions
- For `test_service_opportunities_basic`: confirm how `ServiceRegistry` is initialized and whether there is an existing test fixture or factory for it
- For `test_equipment_stat_injection_move_cost`: confirm `ItemRegistry.get('iron_plate')` path — check if there's a `ContentLoader` or `CatalogRepository` call needed, or if a direct `ItemRegistry.register('iron_plate', weight=12.0, ...)` stub is simpler

## Implementation Notes
Fix 1 — ServiceRegistry fixture:
```python
@pytest.fixture(autouse=True)
def populate_service_registry():
    ServiceRegistry.register(ServiceDefinition(id="shop_1", region_id="hometown", supported_affordances=["buy"], ...))
    yield
    ServiceRegistry.clear()
```

Fix 2 — set target_node_id:
```python
entity.interaction.target_node_id = 100  # any non-None value
```

Fix 3 — ItemRegistry initialization:
```python
# In test setup or conftest for progression tests:
ItemRegistry.register("iron_plate", ItemDefinition(weight=12.0, slot=EquipSlot.TORSO, ...))
```

## Test Summary
Run: `pytest tests/unit/strategic/test_opportunities.py::test_service_opportunities_basic tests/unit/strategic/test_strategic_hardening.py::test_interaction_interrupted_by_damage tests/unit/progression/test_rpg_advancement.py::test_equipment_stat_injection_move_cost -v --tb=short`

## Files Changed
- `tests/unit/strategic/test_opportunities.py` — added `minimal_service_registry` fixture (bootstraps ServiceRegistry with only shop+RecipeRegistry empty); applied to `test_service_opportunities_basic`
- `tests/unit/strategic/test_strategic_hardening.py` — changed `yields_item="WOOD"` to `yields_item="wood"` in ResourceNodeState so the item exists in catalog-bootstrapped CoreItemRegistry
- `tests/unit/progression/test_rpg_advancement.py` — added inline guard to register `iron_plate` in `CoreItemRegistry` if missing (catalog bootstrap omits it)

## Completion Summary
All 3 tests now pass in isolation and when run together in full-suite collection order. Root cause was catalog bootstrap (`seed_phase1_content()` triggered on import of `src.core.registries`) wiping items `"WOOD"` and `iron_plate` from `CoreItemRegistry`, plus craft opportunities from the full recipe catalog filling the top-5 slots before `buy_item`. No production source files were modified.
