---
ticket: TCK-20260609-MIGRATION-TEST-MARKERS
phase: plan
---

# Plan

## New markers added to pyproject.toml (8)
catalog, content_graph, registry_projection, scenario_setup, strict_matrix,
legacy_compat, content_pack, architecture

## Marker application strategy
- New phase 29-34 files: per-file pytestmark at module level
- tests/strict_world_matrix: extend list [worldassembly, strict_matrix]
- tests/arena/ and tests/certification/: conftest.py with pytest_collection_modifyitems hook
  (avoids modifying every existing test file individually)

## Verified selections
- worldassembly: 109 tests
- strict_matrix: 57 tests
- catalog: 10 tests
- scenario_setup: 37 tests
- registry_projection: 9 tests
- architecture: 5 tests
- legacy_compat: 40 tests (arena + certification subset)
