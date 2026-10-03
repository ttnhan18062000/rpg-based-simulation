---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260627-P2K-CONTENT-MATRIX
artifact_type: plan
tags: [content-usage-matrix, auto-discover, plan]
---

# Plan: TCK-20260627-P2K-CONTENT-MATRIX

## Chosen Approach

**Preferred fix**: Auto-discover unregistered content families at matrix import time.

Auto-generation is safe because:
- Directory scan keys are unambiguous (path without extension = family key).
- `DESIGN_ONLY` placeholder entries pass all existing matrix constraint tests.
- The `ValueError` guard in `repository.py` is orthogonal and unaffected.
- Existing handcrafted entries remain unchanged (discovered entries are additive).

## Implementation Steps

### Step 1 — Add `_auto_discover_extra_entries()` to `src/content/matrix.py`

Function signature:
```python
def _auto_discover_extra_entries(
    content_dir: str,
    known_keys: frozenset,
) -> Dict[str, ContentFamilyMatrixEntry]:
```

Scanning logic mirrors `test_matrix_covers_all_content_files` exactly:
- `rglob("*")` over `Path(content_dir)`
- Skip `.gitkeep`
- Top-level structural dirs (`world_modules`, `world_compositions`,
  `simulation_scenarios`) → key is the dir name
- Other `.yaml`/`.yml` files → key is the path without extension
- Skip keys already in `known_keys`
- Return minimal `DESIGN_ONLY` entries with string `"None"` for all metadata fields

### Step 2 — Merge at module level (bottom of `src/content/matrix.py`)

After the `CONTENT_USAGE_MATRIX` dict definition:

```python
_discovered = _auto_discover_extra_entries(
    content_dir="data/content",
    known_keys=frozenset(CONTENT_USAGE_MATRIX.keys()),
)
if _discovered:
    CONTENT_USAGE_MATRIX = {**CONTENT_USAGE_MATRIX, **_discovered}
```

### Step 3 — Add regression tests to `tests/unit/content/test_content_usage_matrix.py`

Tests:
- `test_auto_discover_returns_design_only_for_unknown_file` — unit test with temp dir
- `test_auto_discover_skips_known_keys` — confirms no duplicates
- `test_matrix_auto_populated_covers_all_disk_files` — end-to-end check using
  real `data/content/` dir (mirrors the existing test_matrix_covers_all_content_files logic)

## Constraints

- Do NOT change `src/content/repository.py` — the `ValueError` guard is unaffected.
- Do NOT change `NON_CATALOG_FILES` or `NON_CATALOG_DIRS` in `repository.py`.
- Do NOT change `CANONICAL_FAMILIES` — that is a separate concern.
- Auto-discovered entries must use `content_maturity="ADDITIONAL"` (valid value).
- Auto-discovered entries must use `compile_runtime_consumer="None"` (string).

## Unresolved Questions

None. Approach is unambiguous. Proceeding.

## Deviations

None at time of writing.
