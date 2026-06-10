# Investigation — TCK-20260610-CATALOG-VS-LEGACY-SEMANTICS

## Available Paths

**Legacy path**: `build_scenario_state("COMBAT_ARENA_5V5")` → `ArenaInjector.build_team_battle(base, 5)` → 10 entities, 2 synthetic faction buckets, V2EntityBuilder

**Catalog path**: `CatalogScenarioStateBuilder.build(goblin_camp_pressure)` → frontier_living_world + goblin_camp_conflict, archetype-native entities

## Comparison Design

The paths produce different compositions (5v5 synthetic arena vs. world-assembled goblin conflict), so exact parity is not the goal. The comparison validates that both paths meet the same semantic contract:
- Non-empty entity collection
- All entities alive at tick 0
- Positive combat stats (hp, atk > 0)
- Both pass 3 ticks via CertificationHarness
- Differences (entity count, faction count) are reported but not required to match

## Key Semantic Checks

| Property | What to check |
|---|---|
| entity_count | > 0 for both |
| alive_count | equals entity_count for both at tick 0 |
| combat_stats | hp > 0 and atk > 0 for all entities |
| tick_execution | conformance_passed for 3 ticks |
| faction_diversity | legacy uses legacy enum; catalog uses catalog strings — report both |
