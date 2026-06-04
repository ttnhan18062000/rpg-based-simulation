# Implementation Plan: Phase 22 Schema Fail-Closed and Shorthand Normalization

## Proposed Changes

### Content Schema Component

#### [MODIFY] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/schema.py)
- Set `extra="forbid"` on `CatalogBaseDefinition`'s Pydantic `model_config`.
- Add `extension` and `design_notes` fields to `CatalogBaseDefinition` to ensure they are accepted as valid metadata sections.

### World Assembly Component

#### [MODIFY] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldassembly/schema.py)
- Set `extra="forbid"` on Pydantic `model_config` for `WorldCompositionSpec`, `ModuleRefSpec`, `ProvenanceRecord`, and `ProvenanceManifest`.
- Declare `modules` and `default_perspectives` fields on `WorldCompositionSpec`.
- Add `normalize_modules_shorthand` model validator (using `@model_validator(mode="before")`) to map top-level `modules` lists to `module_refs` and reject mixed configurations.

### World Modules Component

#### [MODIFY] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldmodules/schema.py)
- Set `extra="forbid"` on `WorldModuleSpec` and `ModuleParameterSpec` `model_config`.
- Declare v2 concept list fields on `WorldModuleSpec` (e.g. `biomes`, `ecologies`, `populations`, `relationships`, `resources`, `buildings`, `services`).
- Allow `"worldmodule.v2"` schema version.

#### [NEW] [normalizer.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldmodules/normalizer.py)
- Define `NormalizedWorldModule` dataclass.
- Define `WorldModuleAuthoringNormalizer` containing static `normalize(spec: WorldModuleSpec) -> NormalizedWorldModule` mapping logic.

### Test Components

#### [MODIFY] [test_catalog.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_catalog.py)
- Add tests verifying fail-closed behavior on active and compatibility catalog models (raising `ValidationError` on unknown top-level fields, while permitting them inside nested metadata/extension blocks).

#### [MODIFY] [test_assembly.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldassembly/test_assembly.py)
- Add tests validating composition shorthand normalization, mixed formats rejection, and default perspectives preservation.

#### [MODIFY] [test_modules.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldmodules/test_modules.py)
- Add tests verifying v1/v2 schema parsing support, normalizer execution, invalid type failure, and unknown top-level v2 fields validation failure.

## Verification Plan

### Automated Tests
Execute the following test suites:
- `pytest tests/unit/content/test_catalog.py`
- `pytest tests/unit/worldassembly/test_assembly.py`
- `pytest tests/unit/worldmodules/test_modules.py`
Verify that all existing tests and new validation/normalization test cases pass successfully.
