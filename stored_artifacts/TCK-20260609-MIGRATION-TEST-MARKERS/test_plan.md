---
ticket: TCK-20260609-MIGRATION-TEST-MARKERS
phase: test_plan
---

# Test Plan

Verified with `pytest --collect-only -q -m <marker>`:
- worldassembly: 109 collected, correct
- strict_matrix: 57 collected (subset of worldassembly), correct
- catalog: 10 collected, correct
- scenario_setup: 37 collected, correct
- registry_projection: 9 collected, correct
- architecture: 5 collected, correct
- legacy_compat: 40 collected (arena + certification), correct

All 51 newly-marked test files pass: `pytest tests/unit/runtime/ tests/unit/scenarios/ tests/unit/content/test_migration_map_schema.py tests/architecture/test_no_new_hardcoded_gameplay_truth.py`
