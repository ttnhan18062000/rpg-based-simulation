# Phase 4 Execution Plan

We will implement the world module schema and repository systematically:

1. **Task 4.1**: Define the Pydantic schemas in `src/worldmodules/schema.py`:
   - `ModuleParameterSpec` (exposing type, min, max, default, allowed_values)
   - `WorldModuleSpec` (supporting requires/provides clauses, recipes for regions, populations, resources, and buildings)
   - Enforce enum of module types (terrain, settlement, ecology, economy, conflict, population)
2. **Task 4.2**: Implement `WorldModuleRepository` under `src/worldmodules/repository.py`:
   - Expose lookups, list methods, and diagnostic module hashes/fingerprints.
3. **Task 4.3**: Implement topological sort and dependency checking utility functions.
4. **Task 4.4**: Populate baseline modules under `data/world_modules/` representing template modules.
5. **Task 4.5**: Write focused tests in `tests/unit/worldmodules/` and run the unit test suite.
