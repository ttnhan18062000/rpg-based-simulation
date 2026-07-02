---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260627-P2K-CONTENT-MATRIX
artifact_type: investigation
tags: [content-usage-matrix, auto-generate, registry, authoring-dx]
---

# Investigation: TCK-20260627-P2K-CONTENT-MATRIX

## Problem Statement

Adding a new YAML file to `data/content/` requires manually registering the
family in `CONTENT_USAGE_MATRIX` in `src/content/matrix.py`. No authoring-time
prompt exists — the only feedback is a CI test failure.

## Two Separate Guards

There are two independent mechanisms that enforce consistency between disk and
code, and they must not be conflated:

### 1. `CANONICAL_FAMILIES` check (in `repository.py`)
- Fires: `CatalogRepository.load_all(strict=True)` raises
  `ValueError: Ignored active YAML files found in repository: [...]`
- Covers: files in `data/content/` NOT in `CANONICAL_FAMILIES` paths,
  `NON_CATALOG_DIRS`, or `NON_CATALOG_FILES`
- This guard MUST be preserved per AC.

### 2. `CONTENT_USAGE_MATRIX` check (in `test_content_usage_matrix.py`)
- Fires: `test_matrix_covers_all_content_files` fails
- Covers: disk files not present as keys in `CONTENT_USAGE_MATRIX`
- This is the DX friction point: it only fires in CI, not at authoring time.

## Root Cause

`CONTENT_USAGE_MATRIX` is a hand-maintained dict in `src/content/matrix.py`.
When a new file is added to `data/content/`, the test scans the directory
and compares against the dict keys. Since the new file's key is missing, CI fails.

The `packs/` directory (added in a prior session) demonstrates the pattern:
three files (`packs/swamp_border_pack.yaml`, `packs/frontier_extended_pack.yaml`,
`compatibility/migration_map.yaml`) were added without matrix entries, causing
D10 F6 test failures.

## Auto-Generation Feasibility

The `CONTENT_USAGE_MATRIX` contains rich metadata per family:
- `schema_class`, `repository_index`, `validator_coverage`, `resolver_component`
- `compile_runtime_consumer`, `implementation_state`, `content_maturity`

These cannot be inferred from a directory name alone. However, examining the
existing `DESIGN_ONLY` entries (packs, migration_map, simulation_scenarios)
reveals a safe default: a `DESIGN_ONLY` entry with string `"None"` for
all metadata fields passes every existing matrix constraint test.

**Conclusion**: Auto-generation with `DESIGN_ONLY` placeholders is safe.

## Scanning Logic Match

`test_matrix_covers_all_content_files` uses `content_path.rglob("*")` and:
- For top-level dirs in `{world_modules, world_compositions, simulation_scenarios}`:
  adds the dir name as the key
- For other `.yaml`/`.yml` files: adds the path without extension as the key

The auto-discovery function must mirror this exact logic so auto-generated
keys match what the test expects to find.

## Test Constraint Analysis

All `ContentFamilyMatrixEntry` validator tests pass for auto-discovered
`DESIGN_ONLY` entries:

| Test | Check | DESIGN_ONLY result |
|---|---|---|
| `test_matrix_validation_and_states` | `implementation_state in VALID_STATES` | PASS |
| `test_matrix_validation_and_states` | `schema_class is not None or DESIGN_ONLY` | PASS (None allowed) |
| `test_matrix_validation_and_states` | `validator_coverage is not None` | PASS ("None" string) |
| `test_design_only_family_may_have_no_runtime_consumer` | `consumer in allowed set` | PASS ("None") |
| `test_family_without_declared_consumer_fails_usage_contract` | `DESIGN_ONLY excluded` | PASS |
| `test_runtime_authoritative_requires_evidence` | `RUNTIME_AUTHORITATIVE only` | PASS (not triggered) |

## Selected Approach

Add `_auto_discover_extra_entries(content_dir, known_keys)` to `matrix.py`.
Merge auto-discovered entries into `CONTENT_USAGE_MATRIX` at module import time.
The `ValueError` guard in `repository.py` is unaffected (it checks `CANONICAL_FAMILIES`,
not `CONTENT_USAGE_MATRIX`).

## Related Artifacts

- `src/content/matrix.py` — target file
- `src/content/repository.py` — separate guard, unchanged
- `tests/unit/content/test_content_usage_matrix.py` — test to add regression tests
- `stored_artifacts/TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR/` — prior matrix context
