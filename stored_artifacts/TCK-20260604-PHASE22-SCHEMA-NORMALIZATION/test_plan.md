# Test Plan: Phase 22 Schema Fail-Closed and Shorthand Normalization

## Unit Tests

### 1. Catalog Schema Tests
Add the following test cases in `tests/unit/content/test_catalog.py` (or a dedicated schema test section):
- `test_schema_fail_closed_unknown_field`: Verifies that instantiating a catalog model with an unknown top-level field raises a Pydantic `ValidationError`.
- `test_schema_metadata_nested_field_allowed`: Verifies that placing extra/unknown keys inside the `metadata` or `extension` dictionaries is allowed.
- `test_schema_compatibility_model_fail_closed`: Verifies that compatibility models (e.g. `LegacyEnemyProjectionDefinition`) also raise `ValidationError` when unknown top-level fields are supplied.

### 2. World Composition Normalization Tests
Add the following test cases in `tests/unit/worldassembly/test_assembly.py`:
- `test_composition_shorthand_normalization`: Verifies that setting `modules` as a list of strings on `WorldCompositionSpec` normalizes to `module_refs` correctly.
- `test_composition_mixed_formats_fail`: Verifies that specifying both `modules` shorthand and `module_refs` structured list raises a validation error.
- `test_composition_default_perspectives_preserved`: Verifies that `default_perspectives` is loaded and not dropped.

### 3. World Module Normalization Tests
Add the following test cases in `tests/unit/worldmodules/test_modules.py`:
- `test_v2_module_loading_and_normalization`: Verifies loading a v2 module spec, checking that it normalizes into `NormalizedWorldModule` with v2 fields populated.
- `test_v2_module_unknown_field_fail`: Verifies that unknown fields at the top level of a module YAML/dictionary raise a validation error.
- `test_module_unsupported_type_fail`: Verifies that passing an unregistered `module_type` (e.g. `"economy_unsupported"`) raises a validation error.

## Verification Commands
Run the tests:
- `pytest tests/unit/content/test_catalog.py`
- `pytest tests/unit/worldassembly/test_assembly.py`
- `pytest tests/unit/worldmodules/test_modules.py`
Verify that all tests pass.
