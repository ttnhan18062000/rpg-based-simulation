# Test Plan — TCK-20260610-CATALOG-SCENARIO-BUILDER

## Regression Surface

- `tests/unit/worldassembly/test_assembly.py` — WorldAssemblyResolver must remain unchanged
- `tests/unit/worldassembly/test_archetype_preservation.py` — archetype metadata in CompileContext
- `tests/integration/worldassembly/test_world_entity_spawner.py` — WorldEntitySpawner (no changes)
- `tests/integration/scenarios/test_scenario_setup_resolver.py` — ScenarioSetupResolver (no changes)
- `tests/unit/entities/test_archetype_entity_factory.py` — factory unchanged

## New Tests Required

File: `tests/unit/certification/test_catalog_scenario_state_builder.py`

### Cases

1. `test_build_produces_authoritative_state`
   - Build using `wolf_territory_pressure` scenario
   - Assert result is `AuthoritativeState`
   - Assert `state.entities` is non-empty

2. `test_archetype_entities_have_archetype_id_in_properties`
   - Build using `wolf_territory_pressure` (wolf_pack_small = archetype-native)
   - For each entity with archetype_id in profile, assert `identity.properties["archetype_id"]` is set

3. `test_build_does_not_touch_legacy_arena_builder`
   - Import `src.scenarios.catalog_state_builder` module
   - Assert `build_team_battle` is NOT referenced in the module source

4. `test_build_result_contains_setup_and_expectations`
   - Assert result has `state`, `setup`, `expectations` attributes
   - `setup.scenario_id` matches input scenario ID
   - `expectations` is a `ScenarioExpectations`

5. `test_tick_zero_entities_alive`
   - All spawned entities start alive

## Scoped Pytest Commands

```
pytest tests/unit/certification/test_catalog_scenario_state_builder.py -v
pytest tests/integration/scenarios/test_scenario_setup_resolver.py tests/integration/worldassembly/test_world_entity_spawner.py -v
```

## Anti-Drift Guards

- `CatalogScenarioStateBuilder` must not import from `src.certification.scenarios` (would couple to legacy path)
- `CatalogScenarioStateBuilder` must not use `EntityGenerator` or `V2EntityBuilder` at top level
