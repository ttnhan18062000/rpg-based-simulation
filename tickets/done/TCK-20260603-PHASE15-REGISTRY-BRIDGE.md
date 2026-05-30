# TCK-20260603-PHASE15-REGISTRY-BRIDGE

## Title

Phase 15 — Runtime Registry Bridge with Legacy Projection

## Status

DONE

## Request Summary

Implement a translation bridge in `src/core/registries.py` and `src/core/items.py` that loads the content catalog database and uses it to dynamically bootstrap the legacy runtime registries.

## Scope

- Implement mappers from catalog definitions (`ItemDefinition`, `LegacyEnemyProjectionDefinition`, `RecipeDefinition`, etc.) to legacy dataclasses (`ItemDef`, `EnemyDef`, `RecipeDef`, `RegionDef`, `ServiceDef`).
- Add `bootstrap(cls, data: Dict[str, ItemDefinition])` mapping to `ItemRegistry` in `src/core/items.py`.
- Update `seed_phase1_content()` in `src/core/registries.py` to optionally accept `catalog_repo` and dynamically bootstrap the legacy registries.
- Support logging of the active content source (`catalog` vs `legacy_hardcoded`) and catalog fingerprint.

## Out of Scope

- Removing legacy hardcoded content fallbacks (retained as backup).
- Modifying tick execution or gameplay logic directly.

## Acceptance Criteria

- `seed_phase1_content()` can load directly from `CatalogRepository`.
- It uses the `LegacyEnemyProjection` to reconstruct legacy `EnemyDef` objects.
- It maps items, recipes, regions, and services dynamically from the catalog.
- Legacy hardcoded backup seeding still exists but can be completely bypassed in catalog mode.
- Existing gameplay systems querying the registries query the projected values successfully.
- Tests verify identical catalog/legacy registry contents under seed.

## Related Tickets

- `TCK-20260530-PHASE14-LEGACY-EXPORT`

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`
- `src/core/items.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Executed `pytest tests/unit/core/test_registry_bridge.py tests/unit/core/test_registry_parity.py` (Passed)
- Executed `pytest tests/unit/core/test_rpg_math.py` (Passed)
- Executed `pytest tests/unit/strategic/test_registries.py` (Passed)

## Files Changed

- `src/core/registries.py`
- `src/core/items.py`
- `tests/unit/core/test_registry_bridge.py`
- `tests/unit/core/test_registry_parity.py`

## Completion Summary

- Implemented and verified the translation bridge in `seed_phase1_content` and `ItemRegistry.bootstrap`.
- Added backup and restore protection to core item definitions to prevent test state pollution.
- Established robust unit tests and production data parity verification checks.
