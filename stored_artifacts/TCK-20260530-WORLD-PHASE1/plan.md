# Phase 1 Execution Plan

We will implement the content catalog foundation systematically:

1. **Task 1.1**: Define the Pydantic schemas in `src/content/schema.py` representing:
   - Base properties (`id`, `display_name`, `description`, `tags`, `schema_version`, `deprecated`, `metadata`)
   - `FactionDefinition` (with dynamic mappings like `legacy_engine_bucket`, `alignment_bucket`)
   - `RoleDefinition` (with `legacy_engine_role` and defaults)
   - `StatsProfileDefinition`, `CombatProfileDefinition`, `InventoryProfileDefinition`, `CognitionProfileDefinition`
   - `ResourceDefinition`, `BuildingDefinition`, `ServiceProfileDefinition`, `TerrainDefinition`, `SpawnTableDefinition`, `DefaultCompileProfile`
2. **Task 1.2**: Write the `CatalogRepository` loader in `src/content/repository.py` using `pyyaml` (or existing loaders in the codebase if standard). Expose required lookups and fingerprints.
3. **Task 1.3**: Populate all required legacy definitions under `data/content/` to build the complete `minimal base catalog`.
4. **Task 1.4**: Implement the `CatalogValidator` in `src/content/validator.py` to validate references, types, and schema structures.
5. **Task 1.5**: Write focused tests in `tests/unit/content/` and verify that the test suite passes seamlessly.
