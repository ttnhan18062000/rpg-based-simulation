# TCK-20260530-WORLD-PHASE4

## Title

World Data Refactor Phase 4: World Module Schema and Repository

## Status

DONE

## Request Summary

Establish the structural World Module system under `src/worldmodules`. Define Pydantic schemas for `WorldModuleSpec v1` to enable composing worlds out of reusable structural layout fragments (terrain, settlements, ecology, conflicts, populations, economy), with parameters and requires/provides clauses, explicitly deferring quest seeds. Create the dedicated `WorldModuleRepository` loader, and define topological sorting dependency checking and merge rules preventing silent overwrites.

## Scope

- Define Pydantic schemas in `src/worldmodules/schema.py` representing `WorldModuleSpec` and parameters models supporting standard primitives (string, integer, float, boolean, enum, id_reference).
- Implement `WorldModuleRepository` inside `src/worldmodules/repository.py` to read and load reusable modules from structured directory paths (`data/world_modules/`).
- Define the module topological sorting, dependency checks, and merge rule policies.
- Implement tests verifying module indexing, parameters parsing, duplicates prevention, and dependency validations.

## Out of Scope

- Merging modules into full world compilation specs dynamically (this belongs to the Phase 5 resolver).
- Implementing Quest seeds.

## Acceptance Criteria

- [x] Pydantic `WorldModuleSpec` v1 schema defined in `src/worldmodules/schema.py`.
- [x] Module parameters model supports min/max checks, defaults, and type enforcement.
- [x] Reusable module loader repository (`WorldModuleRepository`) created under `src/worldmodules/repository.py`.
- [x] Directory structures `data/world_modules/<type>/*.yaml` exist and baseline YAML modules are defined.
- [x] topological sort and merge safety rules mapped and tested in `tests/unit/worldmodules/`.
- [x] No runtime behavior changed.

## Related Tickets

- `TCK-20260530-WORLD-PHASE3`

## Related Docs

- `docs/architecture/world_assembly_architecture.md`
- `world_phases_0_10_updated.md`

## Related Code Areas

- `src/worldmodules/schema.py`
- `src/worldmodules/repository.py`

## Assumptions / Open Questions

- Quest contributions are deferred from v1 modules.

## Test Summary

- We will write focused unit tests inside `tests/unit/worldmodules/`.

## Files Changed

- `src/worldmodules/schema.py` (NEW)
- `src/worldmodules/repository.py` (NEW)
- `data/world_modules/...` (NEW files)
