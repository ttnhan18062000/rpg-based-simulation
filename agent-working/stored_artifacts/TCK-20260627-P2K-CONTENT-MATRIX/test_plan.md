---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260627-P2K-CONTENT-MATRIX
artifact_type: test_plan
tags: [content-usage-matrix, auto-discover, testing]
---

# Test Plan: TCK-20260627-P2K-CONTENT-MATRIX

## Scope

Verify that:
1. Auto-discovery populates `CONTENT_USAGE_MATRIX` for unregistered files.
2. Auto-discovered entries pass all existing matrix constraint tests.
3. The `ValueError` guard in `repository.py` is unaffected (regression guard maintained).
4. Existing content pack and gate tests still pass.

## New Tests (in `tests/unit/content/test_content_usage_matrix.py`)

### `test_auto_discovered_entries_are_design_only`
- Create a temp dir with a single unregistered YAML file.
- Call `_auto_discover_extra_entries(tmp_dir, known_keys=frozenset())`.
- Assert the returned entry has `implementation_state="DESIGN_ONLY"`.
- Assert `content_maturity` is a valid maturity state.
- Assert all non-None fields are string `"None"` or equivalent.

### `test_auto_discovered_entries_skip_known_keys`
- Call `_auto_discover_extra_entries("data/content", known_keys=frozenset(CONTENT_USAGE_MATRIX.keys()))`.
- Assert result is empty (all current files are already registered).

### `test_matrix_auto_populated_for_new_file`
- Create a temp dir, copy a minimal valid structure.
- Add a file not in any known_keys.
- Call auto-discover, assert that file's key is present and DESIGN_ONLY.

### `test_content_usage_matrix_covers_all_files_after_auto_discovery`
- Verify `CONTENT_USAGE_MATRIX` (the live module-level dict) covers all files
  currently on disk under `data/content/`. This is a post-implementation check
  that `test_matrix_covers_all_content_files` will pass even without manual updates.

## Regression Tests (Existing, Must Continue to Pass)

| Test | File | What it guards |
|---|---|---|
| `test_strict_load_unknown_extra_file` | `test_catalog.py` | `ValueError: Ignored active YAML files` fires in strict mode |
| `test_matrix_covers_all_content_files` | `test_content_usage_matrix.py` | All disk files in matrix |
| `test_matrix_validation_and_states` | `test_content_usage_matrix.py` | All matrix entries valid states |
| `test_gate_01_content_family_registry_complete` | `test_expansion_gate.py` | CANONICAL_FAMILIES load |
| All other gate tests | `test_expansion_gate.py` | Expansion readiness |

## Command

```bash
pytest tests/unit/content/test_content_usage_matrix.py tests/unit/content/test_catalog.py \
       tests/integration/content/test_expansion_gate.py -v -m "not slow" --tb=short
```
