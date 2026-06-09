# Plan — TCK-20260608-REGISTRY-PARITY-SPLIT

## Steps
1. Read current test_registry_projection_parity.py
2. Add test_compatibility_mode_heuristic_usages_are_detailed (CATALOG_WITH_COMPATIBILITY detail check)
3. Add _build_strict_catalog helper + test_strict_mode_produces_zero_heuristic_usages (CATALOG_STRICT)
4. Add test_legacy_fallback_seeds_only_hardcoded_records (LEGACY_FALLBACK)
5. Run all 8 tests — pass

## Deviations
None.
