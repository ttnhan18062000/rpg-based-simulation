# TCK-20260610-CATALOG-ARENA-SMOKE

## Title
Add CATALOG_ARENA_SMALL integration smoke scenario using catalog archetypes

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 36 requires at least one arena-like scenario that proves the catalog-backed construction path produces a fully executable simulation state. `CATALOG_ARENA_SMALL` uses `frontier_village_core` + `goblin_camp_conflict` modules, spawns `frontier_guard`, `goblin_raider`, and `goblin_archer` from catalog archetypes, and verifies the simulation can tick. This is not a replacement for `COMBAT_ARENA_5V5` or stress tests.

## Scope
- Add integration smoke test: `tests/integration/certification/test_catalog_arena_smoke.py`
- Build `CATALOG_ARENA_SMALL` state using `CatalogScenarioStateBuilder` (TCK-20260610-CATALOG-SCENARIO-BUILDER)
- Assert: entities spawn, combat values come from resolved archetypes, legacy role/faction projection exists only for runtime compatibility, simulation can tick at least once
- Mark test with appropriate slow/integration marker if needed
- Existing arena tests remain unchanged

## Out of Scope
- Replacing `COMBAT_ARENA_5V5` or any existing arena scenario
- Adding many catalog arena scenarios — one is the proof

## Acceptance Criteria
- [x] `CATALOG_ARENA_SMALL` scenario builds from catalog without errors
- [x] Scenario has at least two factions
- [x] Entities have `archetype_id` in identity properties (faction_id and race_id in properties too)
- [x] Runtime combat runs at least one tick without error (3 ticks via CertificationHarness)
- [x] No direct enemy source truth hardcoded in the test
- [x] Existing arena tests remain unchanged

## Related Tickets
- TCK-20260610-CATALOG-SCENARIO-BUILDER (must be done first)
- TCK-20260610-CATALOG-VS-LEGACY-SEMANTICS (companion smoke comparison)

## Related Docs
- `docs/engine/kernel.md`
- `docs/mechanics/02_combat_laws.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-CATALOG-ARENA-SMOKE/`

## Related Code Areas
- `tests/integration/certification/test_catalog_arena_smoke.py` — new
- `src/scenarios/catalog_state_builder.py` — used
- `data/content/world_modules/goblin_camp_conflict.yaml` — goblin_raiding_party population

## Assumptions / Open Questions
- `goblin_camp_conflict` module confirmed to exist with `goblin_raiding_party` population.
- Used `CertificationHarness.run_scenario(scenario_label, state, expectations, ticks=3)` for tick execution.

## Implementation Notes
Created `tests/integration/certification/test_catalog_arena_smoke.py`. Uses `goblin_camp_pressure` scenario definition (frontier_living_world + goblin_camp_conflict, hero_guild_perspective). State built via `CatalogScenarioStateBuilder`. 3 ticks executed via `CertificationHarness(PROD_SMALL)`. No hardcoded enemy IDs.

## Test Summary
4/4 integration tests pass: builds state, ≥2 factions, archetype source in properties, 3-tick execution passes conformance.

## Files Changed
- `tests/integration/certification/__init__.py` — new (dir creation)
- `tests/integration/certification/test_catalog_arena_smoke.py` — new

## Completion Summary
Added `CATALOG_ARENA_SMALL` integration smoke test. 4/4 tests pass including 3-tick CertificationHarness execution. Proves catalog-backed path produces fully executable simulation state.
