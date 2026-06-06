# TCK-20260606-PHASE26-REGISTRY-ADAPTERS-REPAIR

## Title

Phase 26 Registry Adapter Repair

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Make registry projection explicit and testable, not hidden inside heuristic/fallback code.

## Scope

- Move adapter meaning into explicit schema or compatibility data (items, resources, services, enemy projection).
- Add generic registry parity tests to prove catalog records reach runtime registries.
- Ensure adapters use explicit schema fields first, keeping heuristics only for legacy/migration.

## Out of Scope

- Removing all fallback immediately (keep fallback backup paths but ensure catalog mode does not default to heuristics).
- Modifying other phases (20-25 or 27-28) in `world_phase_20_28_repair.md`.

## Acceptance Criteria

- Adapters use explicit schema fields first.
- Heuristics are migration-only, not normal catalog-backed mode.
- Fallback enemy records are not seeded in catalog-backed mode.
- Service defaults are catalog records or compatibility records.
- Adapter errors include source record ID.
- Data-driven parity tests added to `tests/integration/content/test_registry_projection_parity.py`.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added `use_kind`, `class_fit`, `equipment_slot` to `ItemDefinition` schema.
- Added `runtime_kind`, `legacy_id`, `required_tool` to `ResourceDefinition` schema.
- Added `affordances` to `ServiceProfileDefinition` schema.
- Refactored `CatalogToItemRegistryAdapter`, `CatalogToResourceRegistryAdapter`, `CatalogToServiceRegistryAdapter` and `ArchetypeToEnemyRegistryAdapter` in `src/core/registries.py` to check for these explicit fields first.
- Support `migration_mode` (default to True for backward compatibility on legacy seed files) and strict catalog mode (`migration_mode=False`) where heuristics are disabled.
- Prevent default hometown service seeding and default rat enemy seeding in catalog mode.

## Test Summary

- Added unit tests verifying explicit field preference, strict mode validation errors, catalog mode default exclusions, and fallback logging/reporting to `tests/unit/core/test_registry_adapters.py`.
- Added data-driven integration parity tests to `tests/integration/content/test_registry_projection_parity.py` proving items, recipes, services, regions, and enemy projections match catalog definitions.
- All 332 tests passed successfully.

## Files Changed

- `src/core/registries.py`
- `src/content/schema.py`
- `tests/unit/core/test_registry_adapters.py`
- `tests/integration/content/test_registry_projection_parity.py`
- `world_phase_20_28_repair.md`

## Completion Summary

- All acceptance criteria have been fully met. Registry adapters are now fully clean, testable, and explicitly mapped from the content catalog schemas, avoiding silent fallbacks and hardcoded heuristics under catalog-backed execution.
