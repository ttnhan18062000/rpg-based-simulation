---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-CATALOG-SCENARIO-BUILDER
phase: done
date: 2026-06-10
tags: [catalog, scenario, builder]
---

# TCK-20260610-CATALOG-SCENARIO-BUILDER

## Title
Create CatalogScenarioStateBuilder for constructing certification/arena states from catalog archetypes

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Arena and certification tests currently construct `AuthoritativeState` using direct `V2EntityBuilder`, legacy `Faction`, and legacy `EntityRole` assumptions. A `CatalogScenarioStateBuilder` is needed that builds the same state types from catalog archetypes and population recipes — beside the existing legacy builder, not replacing it. This is the Phase 36 migration entry point that proves the catalog-backed path can produce a fully executable scenario state.

## Scope
- Create `src/scenarios/catalog_state_builder.py` with `CatalogScenarioStateBuilder`
- Input: `scenario_id`, `world_composition_id`, `perspective_id`, population recipe refs, spawn layout, runtime content mode
- Internal flow: scenario → composition → module contributions → population resolver → archetype resolver → entity factory (`WorldEntitySpawner`) → `AuthoritativeState`
- Output: `AuthoritativeState`, `ResolvedScenarioSetup`, `ScenarioExpectations`
- Do NOT replace `build_scenario_state()` — add beside it
- Tests: `tests/unit/certification/test_catalog_scenario_state_builder.py`
  - build small hero-vs-goblin state from archetypes
  - build worker/guard village state from population recipe
  - build animal ecology state from wolf population recipe

## Out of Scope
- Replacing or removing existing `build_scenario_state()` or legacy builder
- Changing archetype schema or `ResolvedEntityRuntimeContract`
- Running more than smoke-level simulation ticks in this ticket

## Acceptance Criteria
- [x] `CatalogScenarioStateBuilder` creates a valid `AuthoritativeState`
- [x] Builder uses archetypes/population recipes, not raw legacy enemy IDs
- [x] Builder preserves selected perspective
- [x] Builder produces deterministic entity IDs or stable mapping
- [x] Builder does not replace existing certification builder
- [x] Existing arena tests still pass unchanged

## Related Tickets
- TCK-20260610-CATALOG-ARENA-SMOKE (depends on this)
- TCK-20260610-CATALOG-VS-LEGACY-SEMANTICS (depends on this)
- TCK-20260610-ARCHETYPE-DEFAULT-PATH (WorldEntitySpawner built here — reuse it)
- TCK-20260609-SCENARIO-SETUP-RESOLVER (ScenarioSetupResolver exists — use it)
- TCK-20260609-ARCHETYPE-ENTITY-FACTORY (ArchetypeEntityFactory exists — use it)

## Related Docs
- `docs/engine/authoritative_pipeline.md`
- `docs/engine/kernel.md`
- `docs/parity_ledger/substrate.yaml` (SUB-369)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-CATALOG-SCENARIO-BUILDER/`

## Related Code Areas
- `src/scenarios/catalog_state_builder.py` — new
- `src/worldassembly/entity_spawner.py` — WorldEntitySpawner (reuse)
- `src/scenarios/resolver.py` — ScenarioSetupResolver
- `src/certification/scenarios.py` — existing builder (not modified)

## Assumptions / Open Questions
- `AuthoritativeState` accepts `Dict[int, EntityState]` via `entities` field — confirmed.
- `ScenarioExpectations()` defaults are sufficient for smoke tests.

## Implementation Notes
Created `src/scenarios/catalog_state_builder.py` with `CatalogScenarioStateBuilder` and `CatalogScenarioBuildResult`. Builder composes `ScenarioSetupResolver` → `WorldEntitySpawner` → `AuthoritativeState(tick=0, seed=seed, entities=...)`. No changes to legacy `ArenaInjector` or `build_scenario_state()`.

## Test Summary
8/8 tests pass in `tests/unit/certification/test_catalog_scenario_state_builder.py`. Covers architecture guards (no legacy import, no EntityGenerator), AuthoritativeState production, entity count, tick=0, result fields, archetype_id in identity.properties, all entities alive at tick=0.

## Files Changed
- `src/scenarios/catalog_state_builder.py` — new
- `tests/unit/certification/test_catalog_scenario_state_builder.py` — new
- `docs/parity_ledger/substrate.yaml` — SUB-369 added

## Completion Summary
Created `CatalogScenarioStateBuilder` as the catalog-native scenario construction path, composing existing `ScenarioSetupResolver`, `WorldEntitySpawner`, and `AuthoritativeState`. 8/8 tests pass. Parity ledger SUB-369 added. Legacy builder untouched.
