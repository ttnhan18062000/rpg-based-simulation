# Test Plan: Phase 21 Family Registry & Strict Load Report

## Unit Tests

### Existing catalog tests (`tests/unit/content/test_catalog.py`)
1. Extend `test_base_catalog_loading`:
   - Verify that all canonical content families are declared in `ContentFamilySpec`.
   - Verify `CatalogRepository.load_all()` uses `ContentFamilySpec` to load the repository dictionaries.
2. Add new test cases with temporary content directories:
   - `test_strict_load_missing_required`: Verifies that `load_all(strict=True)` raises `ValueError` if a required family file is missing.
   - `test_strict_load_unknown_extra_file`: Verifies that any undeclared yaml file in `data/content/` is reported as an unknown/ignored file in the load report.
   - `test_strict_load_empty_family`: Verifies that empty yaml files are reported in the load report.
   - `test_strict_load_duplicate_paths`: Verifies that declaring duplicate family paths fails.
   - `test_strict_load_report_fingerprint`: Verifies that the load report has a deterministic fingerprint that changes when content changes.

## Verification Commands
- `pytest tests/unit/content/test_catalog.py`
