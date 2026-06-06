# TCK-20260603-PHASE19-LEGACY-CLEANUP

## Title

Legacy Deprecation and Cleanup

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Phase 19: Clean up legacy dependencies and fallback behaviors, set catalog-backed runtime registries as default, document legacy compatibility fallbacks, and write a regression guard ensuring no new hardcoded items/enemies/recipes/regions are added.

## Scope

- Add documentation and code comments in `src/core/registries.py` highlighting that legacy hardcoded data is for fallback compatibility only, and catalog-backed registries are authoritative.
- Update `seed_phase1_content` in `src/core/registries.py` to check for and load the default content catalog (`data/content`) automatically when no explicit repository is passed, transitioning the default dev/test environment to catalog mode.
- Write a hardcoded-content regression guard test `tests/unit/core/test_hardcoded_regression_guard.py` ensuring that no new hardcoded items, enemies, recipes, resources, services, or regions are introduced without catalog coverage, allowlisting existing legacy assets.
- Verify all unit and integration tests continue to pass.

## Out of Scope

- Deleting legacy hardcoded fallback content at this stage (Phase 19 only marks them as fallback/compatibility).

## Acceptance Criteria

- Legacy registry seed data is clearly commented and documented as compatibility-only.
- `seed_phase1_content()` automatically boots in `"catalog"` mode when `data/content` is present and loads successfully, falling back to legacy mode otherwise.
- A regression guard test exists, allowlisting exactly the 39 existing legacy keys, and fails if any unrecognized definition is added only in the hardcoded maps.
- All tests pass cleanly.

## Related Tickets

- None

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`
- `tests/unit/core/test_hardcoded_regression_guard.py`

## Assumptions / Open Questions

- We assume `data/content/` remains present in the execution environment to allow the default path to initialize catalog-backed registries.

## Implementation Notes

- Added deprecation warnings and documentation headers to `src/core/registries.py`.
- Refactored `seed_phase1_content` to utilize a `_sentinel` default value, allowing automatic loading from `data/content` if present while preserving explicit `None` testing of fallback paths.
- Added `test_hardcoded_regression_guard.py` asserting that no new hardcoded content can be introduced directly in python registries.

## Test Summary

- Run and passed regression guard unit test: `tests/unit/core/test_hardcoded_regression_guard.py`
- Run and passed all core unit tests: `pytest tests/unit/core/` (179 passed)

## Files Changed

- `src/core/registries.py`
- `tests/unit/core/test_hardcoded_regression_guard.py`

## Completion Summary

All tasks under Phase 19 are complete. The default runtime database now seeds directly from the content catalog schemas, and a regression guard strictly prevents developers from adding hidden hardcoded items/enemies/recipes/regions in Python without corresponding catalog specifications.
