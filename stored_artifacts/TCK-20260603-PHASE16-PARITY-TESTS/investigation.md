# Investigation Notes - Phase 16 Parity Tests

## Context & Constraints
* In Phase 15, we built mapping logic from `CatalogRepository` to runtime registries.
* For Phase 16, we need to prove that the catalog configurations support simulation correctness.
* Legacy fallback mode must be preserved. We will support both optional fallback (default) and strict required mode.

## Validation Challenges
* **Cross-Reference Checking**: We need to inspect:
  - `LegacyEnemyProjectionDefinition`: loot table keys, spawn regions.
  - `RecipeDefinition`: ingredients keys, output keys.
  - `ServiceProfileDefinition`: provided_items keys.
  - `RuntimeRegionDefinition`: allowed_enemy_ids keys.
* **Simulation Smoke Test**:
  - We can construct a minimal `AuthoritativeState` and run the simulation engine for 5 ticks.
  - We must ensure `WorldCompiler` and `SimulationDomainLogic` function correctly without hard-law failures under catalog data.
