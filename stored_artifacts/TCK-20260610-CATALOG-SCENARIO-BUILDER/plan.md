# Plan — TCK-20260610-CATALOG-SCENARIO-BUILDER

## Ordered Steps

### Step 1 — Create `src/scenarios/catalog_state_builder.py`

New file with:
- `CatalogScenarioBuildResult` dataclass: `state: AuthoritativeState`, `setup: ResolvedScenarioSetup`, `expectations: ScenarioExpectations`
- `CatalogScenarioStateBuilder`:
  - `__init__(catalog, module_repo, compositions_dir=None)`
  - `build(scenario: SimulationScenarioDefinition, seed=42) -> CatalogScenarioBuildResult`
    1. `ScenarioSetupResolver(catalog, module_repo, compositions_dir).resolve(scenario)` → `setup`
    2. `WorldEntitySpawner().spawn_from_context(setup.world_bundle.compile_context, catalog)` → `entities`
    3. `AuthoritativeState(tick=0, seed=seed, entities=entities)`
    4. Return `CatalogScenarioBuildResult(state, setup, ScenarioExpectations())`

### Step 2 — Add unit tests

File: `tests/unit/certification/test_catalog_scenario_state_builder.py`
Test all 5 cases from test_plan.md using real catalog + module_repo + existing scenario definitions.

### Step 3 — Update parity ledger

Append SUB-369 to `docs/parity_ledger/substrate.yaml`.

### Step 4 — Run tests

```
pytest tests/unit/certification/test_catalog_scenario_state_builder.py -v
```

## Scope Guards

- Do NOT modify `src/certification/scenarios.py`
- Do NOT modify `src/scenarios/resolver.py` or `src/worldassembly/entity_spawner.py`
- Do NOT touch `perf/` or `certification/harness.py`
- `CatalogScenarioStateBuilder` must not import from `src.certification.scenarios`

## Dependency Map

Step 1 → Step 2 → Step 3 → Step 4 (sequential)

## Acceptance Criteria Mapped

- AC1 (valid AuthoritativeState): Step 1
- AC2 (archetypes not raw enemy IDs): Step 1 + Step 2 test_archetype_entities
- AC3 (population recipes): Step 1 (wolf_pack_small is recipe-based)
- AC4 (preserves perspective): Step 1 (setup.perspective_id)
- AC5 (deterministic entity IDs): Step 1 (WorldEntitySpawner base_entity_id=1)
- AC6 (does not replace existing builder): Step 1 (no import from certification.scenarios)
- AC7 (existing arena tests pass): Step 4 (no changes to arena code)

## Deviations
<!-- Fill if any step changes -->
