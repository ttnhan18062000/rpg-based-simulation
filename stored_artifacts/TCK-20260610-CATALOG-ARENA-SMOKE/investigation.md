# Investigation — TCK-20260610-CATALOG-ARENA-SMOKE

## Current Behavior

No `CATALOG_ARENA_SMALL` scenario exists. Existing arena tests use `build_scenario_state()` (legacy V2EntityBuilder path) + `CertificationHarness.run_scenario()`.

`CatalogScenarioStateBuilder` (TCK-20260610-CATALOG-SCENARIO-BUILDER) now exists and can produce an `AuthoritativeState` from a catalog scenario definition.

`CertificationHarness.run_scenario(scenario_id, state, expectations, ticks=N)` runs ticks — scenario_id is a string label (any value), state is `AuthoritativeState`, expectations is `ScenarioExpectations`.

## Available Components

- `CatalogScenarioStateBuilder` in `src/scenarios/catalog_state_builder.py`
- `goblin_camp_pressure` scenario in `frontier_scenarios.yaml` uses `frontier_living_world` composition + `goblin_camp_conflict` module (goblin_raiding_party population = goblin_raider + goblin_archer archetypes)
- `frontier_living_world` also includes `frontier_village_core` (frontier_guard archetype)
- At least two factions: `goblin_warband` + `town_council`
- `PROD_SMALL` profile available from `src/config/profiles`

## Gap

No integration smoke test at `tests/integration/certification/test_catalog_arena_smoke.py`.

## Fix Design

Simple integration test:
1. Build `goblin_camp_pressure` scenario via `CatalogScenarioStateBuilder`
2. Assert entity/faction properties (archetype source IDs)
3. Run `CertificationHarness.run_scenario("CATALOG_ARENA_SMALL", state, expectations, ticks=3)`
4. Assert `result.conformance_passed`
