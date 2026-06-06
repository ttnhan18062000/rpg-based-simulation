# TCK-20260605-PHASE26-REGISTRY-ADAPTERS

## Title

World content projection and runtime registry adapters

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Make world content families such as items, recipes, regions, resources, services, and buildings move through explicit adapters, not scattered heuristics, extracting registry adapters. Prove parity with tests.

## Scope

- Create `CatalogToItemRegistryAdapter`
- Create `CatalogToRecipeRegistryAdapter`
- Create `CatalogToServiceRegistryAdapter`
- Create `CatalogToRegionRegistryAdapter`
- Create `CatalogToResourceRegistryAdapter`
- Create `ArchetypeToEnemyRegistryAdapter`
- Refactor `seed_phase1_content()` in `src/core/registries.py` to use these adapters.
- Implement registry parity tests verifying catalog records reach the runtime registries.

## Out of Scope

- Implementing Phase 27 or 28.
- Modifying non-content simulation domains.

## Acceptance Criteria

- Registry seeding no longer contains category/class-fit/resource heuristics inline.
- Each registry has one adapter.
- Each adapter has unit tests.
- Existing hardcoded fallback still works in fallback mode.
- Catalog-backed mode is deterministic.
- Adapter errors include source record ID.
- All active item/recipe/service/region/enemy records project to their registries.
- Test is data-driven, located in `tests/unit/core/test_registry_parity.py` or similar.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`
- `tests/unit/core/test_registry_parity.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Extracted all six adapters and defined `AdapterError` inside `src/core/registries.py`.
- Refactored `seed_phase1_content` to instantiate and execute these adapters.

## Test Summary

- Added 8 unit tests in `tests/unit/core/test_registry_adapters.py` testing each adapter.
- Added data-driven registry parity test `test_all_catalog_records_project_to_registries` in `tests/unit/core/test_registry_parity.py`.
- All unit tests pass.

## Files Changed

- `src/core/registries.py`
- `tests/unit/core/test_registry_adapters.py`
- `tests/unit/core/test_registry_parity.py`

## Completion Summary

- Clean implementation of registry adapters and test suites. Parity is successfully verified.
