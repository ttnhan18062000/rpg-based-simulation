# Milestone 77 Test Plan

## Unit Tests

### `tests/unit/lab/test_labrun_manifest.py`
- `test_valid_manifest_loads`: Verifies full compliant spec parses correctly.
- `test_missing_required_fields`: Verifies missing identifiers raise Pydantic errors.
- `test_invalid_types_or_budgets`: Checks negative values are rejected.

### `tests/unit/lab/test_lab_artifact_layout.py`
- `test_layout_directories_creation`: Verifies subfolders are created.
- `test_traversal_boundary_prevention`: Verifies traversal checks.
- `test_overwrite_prevention`: Checks directory clash raises error.
- `test_index_rebuild`: Verifies index compiles correctly.
