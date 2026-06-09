---
ticket: TCK-20260609-MIGRATION-TEST-MARKERS
phase: investigation
---

# Investigation

## Existing markers
worldassembly, slow, extra_slow, world_long_run, legacy_characterization, v2_contract,
differential, intentional_divergence, regression, certification, perf, integration,
e2e, strategic_loop.

## Files already having pytestmark
- 7 worldassembly test files (from ticket 8)
- tests/integration/content/test_strict_world_matrix.py (worldassembly)

## Files with no markers (need new ones)
- tests/unit/content/test_migration_map_schema.py
- tests/integration/content/test_active_data_consumer.py
- tests/unit/scenarios/test_scenario_schema.py
- tests/unit/scenarios/test_scenario_modifier_apply.py
- tests/integration/scenarios/test_scenario_setup_resolver.py
- tests/unit/runtime/test_registry_bootstrap_modes.py
- tests/architecture/test_no_new_hardcoded_gameplay_truth.py
- tests/arena/ (all files) — via conftest.py hook
- tests/certification/ (all files) — via conftest.py hook
