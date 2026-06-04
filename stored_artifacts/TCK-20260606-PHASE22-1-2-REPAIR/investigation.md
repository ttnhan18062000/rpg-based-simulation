# Investigation - Phase 22.1 & 22.2 Schema and Normalization Repair

## Current State Analysis

1. **Fail-Closed Schemas**:
   - `WorldCompositionSpec` and `ModuleRefSpec` are defined in `src/worldassembly/schema.py` and configure `extra="forbid"`.
   - `WorldModuleSpec` and `ModuleParameterSpec` are defined in `src/worldmodules/schema.py` and configure `extra="forbid"`.
   - This ensures that if any unknown top-level field is passed to these Pydantic models, validation will fail.

2. **Real Content Files**:
   - The real composition files are under `data/content/world_compositions/` (e.g., `frontier_living_world.yaml`).
   - The real module files are under `data/content/world_modules/` (e.g., `frontier_village_core.yaml`).
   - We need to write tests that load these files directly and test validation.

3. **Composition Normalization**:
   - `WorldCompositionNormalizer.normalize(composition)` is defined in `src/worldassembly/schema.py`.
   - It validates shorthand `modules` and converts it to `module_refs`.
   - If both `modules` shorthand and `module_refs` dictionary list exist, it raises a `ValueError`.
   - We must make sure that `default_perspectives` is preserved when normalization completes and that the resulting `NormalizedWorldComposition` is correctly constructed.
   - Let's check `NormalizedWorldComposition` fields:
     - `schema_version`
     - `world_id`
     - `name`
     - `description`
     - `catalog_refs`
     - `module_refs`
     - `default_perspectives`
     - `global_parameters`
     - `generation_seed`
     - `validation_profile`
   - All these fields exist on `NormalizedWorldComposition`. We should verify that `default_perspectives` correctly survives from the input yaml into `NormalizedWorldComposition` and then into `ResolvedWorldBundle`.
