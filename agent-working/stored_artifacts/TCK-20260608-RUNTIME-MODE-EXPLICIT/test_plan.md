---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-RUNTIME-MODE-EXPLICIT
artifact_type: test_plan
tags: [runtime, mode, explicit]
---

# Test Plan — TCK-20260608-RUNTIME-MODE-EXPLICIT

## tests/unit/content/test_runtime_content_mode.py (new)
- `test_exactly_four_modes` — enum has exactly 4 values
- `test_all_four_mode_names_exist` — CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK, TEST_MANUAL present
- `test_migration_and_v2_removed` — MIGRATION and V2 absent
- `test_catalog_strict_rejects_heuristic_use_kind` — CATALOG_STRICT raises AdapterError on heuristic
- `test_catalog_with_compatibility_allows_heuristic` — CATALOG_WITH_COMPATIBILITY returns items with heuristic_count > 0
- `test_legacy_fallback_seeds_hardcoded_records` — no-catalog seed produces legacy items
- `test_test_manual_mode_does_not_require_catalog` — no-catalog seed with TEST_MANUAL succeeds

## tests/integration/content/test_registry_projection_parity.py (updated)
- Fixture now seeds with CATALOG_WITH_COMPATIBILITY instead of MIGRATION
- All 5 parity tests pass unchanged

## Result: 12/12 passed
