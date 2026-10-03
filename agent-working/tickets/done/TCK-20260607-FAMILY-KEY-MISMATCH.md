---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-FAMILY-KEY-MISMATCH
phase: done
date: 2026-06-07
tags: [family, key, mismatch]
---

# TCK-20260607-FAMILY-KEY-MISMATCH

## Title
Fix FAMILY_TO_SHORT / CONTENT_USAGE_MATRIX naming mismatch silencing region dead-record validation

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`FAMILY_TO_SHORT["world.regions"]` in `reference_graph.py` maps to `"region"`. In `validator.py`, the dead-record check derives the matrix key via `key.replace(".", "/")` → `"world/regions"`. But `CONTENT_USAGE_MATRIX` uses the key `"world/runtime_regions"` (matching the file path). These don't match, so the lookup at `validator.py:630` silently falls through and dead-record validation is skipped for ALL region records.

## Scope

### Root Cause

`CANONICAL_FAMILIES` entry:
```python
ContentFamilySpec("world.regions", "world/runtime_regions.yaml", RuntimeRegionDefinition, "regions")
```

`FAMILY_TO_SHORT`:
```python
"world.regions": "region"
```

Validator derivation (`validator.py:626-627`):
```python
family_key = key.replace(".", "/")   # "world.regions" → "world/regions"
```

`CONTENT_USAGE_MATRIX` key: `"world/runtime_regions"` ≠ `"world/regions"` → `continue` (silent skip).

### Fix Options

**Option A (preferred — minimal change):** Add an explicit override mapping in `validator.py`:
```python
FAMILY_KEY_OVERRIDES = {
    "world/regions": "world/runtime_regions",
}
# after derivation:
family_key = FAMILY_KEY_OVERRIDES.get(family_key, family_key)
```

**Option B:** Rename the `CONTENT_USAGE_MATRIX` key to `"world/regions"` and update `test_matrix_covers_all_content_files` to use an explicit override there (since the test derives the key from the file path `world/runtime_regions.yaml` → `"world/runtime_regions"`).

**Option C:** Change `FAMILY_TO_SHORT["world.regions"]` to something that produces the right derived key — but this would rename the concept shorthand "region" which affects graph nodes and edges.

Option A is the least invasive and most explicit fix for the hotfix scope.

## Out of Scope
- Do not rename graph concept shorthand "region"
- Do not restructure CONTENT_USAGE_MATRIX key conventions broadly
- Do not add dead-record tests for regions (separate coverage concern)

## Acceptance Criteria
- [ ] `validator._validate_dead_active_data` correctly finds the matrix entry for `concept == "region"`
- [ ] No silent skip for region concept in dead-record validation
- [ ] `test_matrix_covers_all_content_files` still passes
- [ ] All 173 phase-specific tests still pass
- [ ] Add test: `test_dead_record_validator_covers_region_concept` asserting the matrix lookup succeeds for a known region record

## Related Tickets
- TCK-20260607-VALIDATOR-MATURITY-POLICY (companion hotfix, same validator file)

## Related Docs
- world_phase_20_28_repair.md Phase 23

## Related Stored Artifacts
None

## Related Code Areas
- `src/content/validator.py:623-630`
- `src/content/reference_graph.py` — FAMILY_TO_SHORT
- `src/content/matrix.py` — CONTENT_USAGE_MATRIX key for world/runtime_regions
- `tests/unit/content/test_content_usage_matrix.py`

## Assumptions / Open Questions
- Are there other FAMILY_TO_SHORT keys with the same mismatch? The audit script confirms only `"world.regions"` is affected.

## Implementation Notes
Option A requires adding ~3 lines to `validator.py`. No schema changes.

## Test Summary
Run `pytest tests/unit/content/ -q` — 173 pass expected.

## Files Changed
- `src/content/validator.py` (add FAMILY_KEY_OVERRIDES)
- `tests/unit/content/test_content_usage_matrix.py` (add coverage assertion)

## Completion Summary
Done. 169 tests pass.
