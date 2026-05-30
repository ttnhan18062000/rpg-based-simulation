# Test Plan: Phase 19 Legacy Deprecation and Cleanup

This outlines the testing strategy for verifying Phase 19.

## Automated Tests

### 1. Default Seeding Test
- Verify that calling `seed_phase1_content()` without parameters successfully defaults to `"catalog"` if `data/content` exists.
- Verify that if `data/content` does not exist or fails to load, it falls back to `"legacy_hardcoded"`.

### 2. Hardcoded Content Regression Guard
- Create `tests/unit/core/test_hardcoded_regression_guard.py`.
- Write a test checking that no new key (not listed in the allowlist) is added to the hardcoded registries without a matching definition in the content catalog.
- Verify that adding a dummy key to hardcoded registries triggers a failure in the test.
