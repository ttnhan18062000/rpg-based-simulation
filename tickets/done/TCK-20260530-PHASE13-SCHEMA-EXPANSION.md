# TCK-20260530-PHASE13-SCHEMA-EXPANSION

## Title

Phase 13 — Runtime Content Catalog Schema Expansion

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 13 as specified in `world_phases_11_19.md`. Extend the content catalog schema definitions to include items, recipes, enemies, and runtime regions, load them via `CatalogRepository`, and support cross-reference validation in `CatalogValidator`.

## Scope

- Add dynamic Pydantic definitions for `ItemDefinition`, `EnemyDefinition`, `RecipeDefinition`, and `RuntimeRegionDefinition` under `src/content/schema.py`.
- Update `CatalogRepository` in `src/content/repository.py` to support loading and indexing:
  - `data/content/items.yaml` -> `ItemDefinition`
  - `data/content/enemies.yaml` -> `EnemyDefinition`
  - `data/content/recipes.yaml` -> `RecipeDefinition`
  - `data/content/regions.yaml` -> `RuntimeRegionDefinition`
- Add relational cross-reference checks to `CatalogValidator` in `src/content/validator.py` ensuring references do not dangle:
  - Enemy loot drop `item_id` references exist in items.
  - Spawn region `spawn_regions` references exist in runtime regions.
  - Recipe output and ingredient `item_id` references exist in items.
  - Recipe required services exist.
  - Runtime region `allowed_enemy_ids` exist in enemies.

## Out of Scope

- Exporting full legacy game content (Phase 14).
- Seeding runtime registries (Phase 15).

## Acceptance Criteria

- All new schemas load cleanly in `CatalogRepository`.
- Relational validation errors are caught and returned in `CatalogValidator`.
- Unit tests verify schema validation, repository load paths, and cross-reference checks.

## Related Tickets

- `TCK-20260530-PHASE12-RESOLVE-CLI-INTEGRATION`

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/content/schema.py`
- `src/content/repository.py`
- `src/content/validator.py`
- `tests/unit/content/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Pydantic's `def` field restriction handled via `alias="def"` and model loading.

## Test Summary

- Added `tests/unit/content/test_runtime_catalog.py` which fully validates loader routing and cross-reference validation errors (CAT-REL-005 to CAT-REL-010). All tests passing.

## Files Changed

- `src/content/repository.py`
- `src/content/validator.py`
- `src/worldgeneration/generator.py`
- `tests/unit/content/test_runtime_catalog.py`

## Completion Summary

- Successfully completed Phase 13 of the RPG Simulation balance & unification direction. Extended CatalogRepository with full lookups and collections routing for dynamic items, recipes, enemies, and regions. Integrated relational diagnostic checks to CatalogValidator. Added pydantic validation support to the procedural world generator, and fully verified functionality with a comprehensive test suite.
