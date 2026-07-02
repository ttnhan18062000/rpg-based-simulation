---
status: active
artifact_type: test_plan
ticket_id: TCK-20260627-P3D-CATALOG-BROWSER
date: 2026-06-27
---

# Test Plan — TCK-20260627-P3D-CATALOG-BROWSER

## Scope

Tooling addition only. No engine behavior changes.

## Test Strategy

### 1. Smoke test — `make catalog-list` exits 0 and produces output

```bash
make catalog-list
```

Expected: exit code 0; stdout contains at least one section header and at least one
catalog ID for each of: biomes, ecologies, populations, factions, regions.

### 2. Script direct invocation

```bash
python3 tools/catalog_list.py
```

Same expectations as above.

### 3. `pytest tests/docs/ -x -q`

Run the existing doc tests to verify no regression from authoring_guide.md edits.

## No New Unit Tests Required

`tools/catalog_list.py` is a read-only diagnostic CLI that delegates entirely to
`CatalogRepository.get_all_ids_by_type()`, which is already tested by the
`lane-catalog` suite. Adding a test for the script itself (mocking sys.stdout) would
be superficial coverage — the integration test (`make catalog-list` exit 0) is the
meaningful gate.

## Regression Risk

Low. The script does not mutate any catalog state, does not affect `load_all()` behavior,
and does not change any existing method signatures. The Makefile addition is purely
additive. The authoring guide append does not alter any existing content.
