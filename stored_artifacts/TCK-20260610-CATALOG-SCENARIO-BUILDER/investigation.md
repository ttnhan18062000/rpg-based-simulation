# Investigation — TCK-20260610-CATALOG-SCENARIO-BUILDER

## Current Behavior

No `CatalogScenarioStateBuilder` exists. Arena/certification tests construct `AuthoritativeState` by:
- `ArenaInjector.build_team_battle()` (`src/certification/scenarios.py`) — uses `EntityGenerator.spawn_hero()` / `spawn_monster()`, legacy `Faction`/`EntityRole` enums, direct `V2EntityBuilder`
- `PressureInjector.inject_entities()` — pure `V2EntityBuilder`

These are not catalog-backed. The catalog-native path that exists:
1. `ScenarioSetupResolver` (`src/scenarios/resolver.py`) — resolves `SimulationScenarioDefinition` → `ResolvedScenarioSetup` (with `world_bundle: ResolvedWorldBundle`)
2. `WorldEntitySpawner` (`src/worldassembly/entity_spawner.py`) — converts `CompileContext.entities` → `Dict[int, EntityState]` via `ArchetypeEntityFactory`
3. `AuthoritativeState` (`src/core/state.py`) — frozen dataclass, `tick: int` + `seed: int` required, `entities: Dict[int, EntityState]` defaults to `{}`

The gap: nothing composes these three into a single builder that produces an `AuthoritativeState` from a scenario definition.

## Key APIs

### AuthoritativeState
```python
AuthoritativeState(tick=0, seed=42, entities={...})
```

### ScenarioSetupResolver
```python
resolver = ScenarioSetupResolver(catalog, module_repo, compositions_dir)
setup: ResolvedScenarioSetup = resolver.resolve(scenario_def)
# setup.world_bundle.compile_context.entities: Dict[str, ResolvedEntityProfile]
```

### WorldEntitySpawner
```python
spawner = WorldEntitySpawner()
entities: Dict[int, EntityState] = spawner.spawn_from_context(ctx, catalog)
```

### SimulationScenarioDefinition
```python
SimulationScenarioDefinition(
    id="wolf_territory_pressure",
    world_composition="frontier_living_world",
    perspective="hero_guild_perspective",
    focus_modules=["wolf_den_near_forest"],
    initial_conditions={}
)
```

## Available Test Scenarios

Existing catalog scenarios in `data/content/simulation_scenarios/frontier_scenarios.yaml`:
- `wolf_territory_pressure` — `frontier_living_world` + `wolf_den_near_forest`, wolf_pack_small (archetype-native)
- `goblin_camp_pressure` — `frontier_living_world` + `goblin_camp_conflict`, hero_guild_perspective
- `old_mine_recovery` — `frontier_living_world` + `old_mine_resource_loop`

## Gap

`src/scenarios/catalog_state_builder.py` does not exist. No component composes `ScenarioSetupResolver` + `WorldEntitySpawner` + `AuthoritativeState` construction.

## Fix Design

Create `src/scenarios/catalog_state_builder.py`:
- `CatalogScenarioBuildResult` — typed result container (state, setup, expectations)
- `CatalogScenarioStateBuilder` — composes the three existing components

## Risks

- `ScenarioSetupResolver._load_composition()` reads `data/content/world_compositions/{composition_id}.yaml` — tests must use existing compositions
- `WorldEntitySpawner` may fall through to legacy guard for profiles without `archetype_id` (legacy roles) — expected behavior, not an error
- `ScenarioExpectations` has no catalog-specific fields — use defaults for now

## Parity Ledger

No existing entry covers `CatalogScenarioStateBuilder` — new behavior, will add to `substrate.yaml` as SUB-369.
