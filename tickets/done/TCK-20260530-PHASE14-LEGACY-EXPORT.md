---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260530-PHASE14-LEGACY-EXPORT
phase: done
date: 2026-05-30
tags: [phase14, legacy, export]
---

# TCK-20260530-PHASE14-LEGACY-EXPORT

## Title

Phase 14 — Adopting Layered Catalog and Populating Profiles

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Copy the designed YAML files from `new_data_design/` to `data/content/` (overwriting and reorganizing the catalog directory structure) and populate all necessary baseline profiles (combat, cognition, needs, senses) for all races and archetypes.

## Scope

- Redefine catalog schemas in `src/content/schema.py` to match the layered world data direction.
- Copy all files from `new_data_design/` to `data/content/` maintaining directory partitions.
- Update `CatalogRepository` and `CatalogValidator` for layered loading and verification.
- Ensure all exported data passes `CatalogValidator` validations.

## Out of Scope

- Replacing runtime registries or bootstrap logic (Phase 15).
- Changing active gameplay systems.

## Acceptance Criteria

- `CatalogRepository` successfully loads all configurations from `data/content/` under the new layered schema structure.
- `CatalogValidator` returns zero errors on the expanded catalog.
- Legacy bootstrap in `src/core/registries.py` remains active and untouched (no behavioral changes yet).

## Related Tickets

- `TCK-20260530-PHASE13-SCHEMA-EXPANSION`

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/registries.py`
- `data/content/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Corrected `SkillProfileDefinition` and `RecipeDefinition` schema fields to match actual data layouts (`skills: List[str]` and `ingredients: Dict[str, int]`).
- Resolved all 13 semantic validation errors in the live database files by declaring missing compatible roles, missing items, missing themes, and missing stats profiles.

## Test Summary

- Added comprehensive relational validation test suite `tests/unit/content/test_layered_catalog.py` covering rules `CAT-REL-011` through `CAT-REL-019`.
- Fixed directory structure dependencies in `tests/unit/content/test_catalog.py` and `tests/unit/content/test_runtime_catalog.py`.
- Executed `pytest tests/unit/content/` successfully with all 5 unit tests passing.
- Validated the live catalog with `CatalogValidator` verifying 0 active errors.

## Files Changed

- `src/content/schema.py`
- `src/content/validator.py`
- `data/content/compatibility/legacy_enemy_projection.yaml`
- `new_data_design/compatibility/legacy_enemy_projection.yaml`
- `data/content/world/items.yaml`
- `new_data_design/world/items.yaml`
- `data/content/social/roles.yaml`
- `new_data_design/social/roles.yaml`
- `data/content/entities/stat_profiles.yaml`
- `new_data_design/entities/stat_profiles.yaml`
- `data/content/foundation/themes.yaml`
- `new_data_design/foundation/themes.yaml`
- `tests/unit/content/test_catalog.py`
- `tests/unit/content/test_runtime_catalog.py`
- `tests/unit/content/test_layered_catalog.py`

## Completion Summary

- The catalog data has been successfully restructured to follow the Layered World Data Direction.
- Pydantic models in `src/content/schema.py` and repository loading in `src/content/repository.py` match the partitioned directory structures.
- Semantic validations are passing cleanly with zero relational errors.
