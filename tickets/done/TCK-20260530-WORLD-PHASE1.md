# TCK-20260530-WORLD-PHASE1

## Title

World Data Refactor Phase 1: Content Catalog Foundation

## Status

DONE

## Request Summary

Establish the Content Catalog Foundation (`src/content`). Define static schemas for factions, roles, profiles (stats, combat, inventory, cognition), resources, buildings, services, terrain, and spawn tables. Create the repository layer to load definitions from files and resolve lookup operations, validate semantic definitions independently, and populate a minimal base catalog matching all legacy configurations.

## Scope

- Define pydantic-based schemas for all catalog definition types under `src/content/schema.py`.
- Implement `CatalogRepository` under `src/content/repository.py` to read and load YAML files from `data/content/`.
- Provide read-only lookup APIs and validate that duplicate IDs or malformed schemas fail.
- Implement the validator system `CatalogValidator` in `src/content/validator.py`.
- Populate a base catalog matching legacy systems under `data/content/` (reproducing the defaults and mappings identified in Phase 0).

## Out of Scope

- Modifying `src/worldbuilding/compiler.py` or runtime layers.
- Interacting with `WorldSpec` or resolving gameplay semantics dynamically.

## Acceptance Criteria

- [x] Content catalog Pydantic schemas exist under `src/content/schema.py`.
- [x] Loader/Repository (`CatalogRepository`) exists under `src/content/repository.py`.
- [x] Catalog validator (`CatalogValidator`) exists under `src/content/validator.py` returning warning/error reports.
- [x] Base catalog definition files loaded under `data/content/*.yaml`.
- [x] Tests verify that lookup, duplicate-checking, and schema mismatch validation function flawlessly.
- [x] No runtime behavior changed.

## Related Tickets

- `TCK-20260530-WORLD-PHASE0`

## Related Docs

- `docs/architecture/world_assembly_architecture.md`
- `world_phases_0_10_updated.md`

## Related Code Areas

- `src/content/schema.py`
- `src/content/repository.py`
- `src/content/validator.py`

## Assumptions / Open Questions

- We will structure the schema cleanly using modern Pydantic patterns matching the `clean-code` guidelines.

## Test Summary

- We will write isolated unit tests inside `tests/unit/content/` to ensure correctness without overloading the system.

## Files Changed

- `src/content/schema.py` (NEW)
- `src/content/repository.py` (NEW)
- `src/content/validator.py` (NEW)
- `data/content/...` (NEW YAML files)
