---
ticket: TCK-20260609-REGISTRY-BOOTSTRAP-MODES
phase: test_plan
---

# Test Plan

9 tests in tests/unit/runtime/test_registry_bootstrap_modes.py, all pass.

| Test | Validates |
|---|---|
| test_strict_mode_raises_hardcoded_fallback_error_when_no_catalog | CATALOG_STRICT + no catalog → HardcodedFallbackError |
| test_compat_mode_raises_hardcoded_fallback_error_when_no_catalog | CATALOG_WITH_COMPATIBILITY + no catalog → HardcodedFallbackError |
| test_legacy_fallback_mode_seeds_hardcoded_registries | LEGACY_FALLBACK + no catalog → fallback_used=True, enemies populated |
| test_test_manual_mode_seeds_empty_registries_without_catalog | TEST_MANUAL + no catalog → empty registries, no error |
| test_compat_mode_with_catalog_populates_enemies_via_projection | mock catalog with projection → compat_counts has enemy |
| test_catalog_path_with_empty_mock_seeds_only_hometown_region | empty catalog → region=1 (hometown injected) |
| test_content_source_report_totals_are_consistent | total_fallback = sum of fallback_counts |
| test_hardcoded_fallback_error_mode_attribute | error carries .mode and detail |
| test_content_source_report_is_frozen | ContentSourceReport is immutable |
