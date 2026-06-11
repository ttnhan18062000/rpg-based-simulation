---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260603-PHASE19-LEGACY-CLEANUP
artifact_type: plan
tags: [phase19, legacy, cleanup]
---

# Implementation Plan: Phase 19 Legacy Deprecation and Cleanup

This plan covers the transition of the runtime simulation registries to default catalog-backed seeding, marking legacy seed maps as compatibility fallbacks, and adding a regression guard.

## Proposed Changes

### Core Registries Seeding
- Modify `src/core/registries.py` to add documentation comments highlighting that legacy hardcoded seed maps are for fallback compatibility only, and catalog-backed mode is authoritative.
- Update `seed_phase1_content` to load from `"data/content"` by default if `catalog_repo` is `None` and the directory exists.

### Hardcoded content regression guard
- Create `tests/unit/core/test_hardcoded_regression_guard.py` containing a test case that:
  - Asserts that all keys present in the legacy hardcoded maps (`items`, `resources`, `enemies`, `recipes`, `services`, `regions`) are either present in the content catalog or explicitly listed in the allowlist of 39 legacy assets.
  - If any key is added that is not in the catalog and not in the allowlist, the test fails.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/core/test_hardcoded_regression_guard.py`
- Run the full test suite (`pytest tests/unit/` and `pytest tests/integration/`) to ensure no tests fail due to the default flip.
