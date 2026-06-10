# TCK-20260610-FALLBACK-RESTRICT-MODES — Test Plan

## New tests (test_fallback_restrict_modes.py)
1. seed_phase1_content with CATALOG_STRICT + no catalog → raises FallbackRestrictedError
2. seed_phase1_content with CATALOG_WITH_COMPATIBILITY + no catalog → raises FallbackRestrictedError
3. seed_phase1_content with LEGACY_FALLBACK + no catalog → succeeds (no raise)
4. Error message contains mode value
5. Error message contains catalog path suggestion ("data/content")
6. FallbackRestrictedError importable from bootstrap
7. HardcodedFallbackError importable from bootstrap (backward compat)
8. HardcodedFallbackError is subtype of FallbackRestrictedError

## Existing tests that must still pass
All 7 tests in test_registry_bootstrap_modes.py must pass unchanged.

## Mode coverage
| Mode | bootstrap_registries | seed_phase1_content |
|---|---|---|
| CATALOG_STRICT + no catalog | raises ✓ | raises (new) |
| CATALOG_WITH_COMPATIBILITY + no catalog | raises ✓ | raises (new) |
| LEGACY_FALLBACK + no catalog | succeeds ✓ | succeeds ✓ |
| TEST_MANUAL | empty ✓ | n/a (catalog_repo=None short-circuits) |
