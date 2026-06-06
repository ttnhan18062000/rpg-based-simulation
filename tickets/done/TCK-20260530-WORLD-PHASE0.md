# TCK-20260530-WORLD-PHASE0

## Title

World Data Refactor Phase 0: Architecture Inventory and Boundary Freeze

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish and freeze the architecture before world-data refactor implementation begins. This includes creating a detailed Architecture Decision Record (ADR), auditing all hardcoded content and semantic assumptions within the compiler and runtime engine, and deciding the repository layout for `WorldCompositionSpec`.

## Scope

- Create a comprehensive architecture decision record (`docs/architecture/world_assembly_architecture.md`) defining package boundaries, roles, and forbidden dependency paths.
- Audit all files in `src/` for hardcoded content/default variables and write a comprehensive hardcoded semantic inventory (`staging_artifacts/TCK-20260530-WORLD-PHASE0/hardcoded_inventory.md`).
- Decide and document the layout strategy for `worldcomposition.v1` (`docs/architecture/world_repository_layout.md`).
- Make absolutely zero runtime code changes.

## Out of Scope

- Implementing new schema loading or parsing logic.
- Resolving/modifying any of the hardcoded defaults at this stage.
- Modifying standard simulation execution behavior.

## Acceptance Criteria

- [x] Architecture boundary/ADR document completed and saved at `docs/architecture/world_assembly_architecture.md`.
- [x] Hardcoded semantic inventory completed and saved at `staging_artifacts/TCK-20260530-WORLD-PHASE0/hardcoded_inventory.md`.
- [x] `WorldCompositionSpec` repository strategy decided and saved at `docs/architecture/world_repository_layout.md`.
- [x] `CompileProfileResolver` location officially defined inside `src/worldassembly`.
- [x] No runtime behavior changed (existing tests must pass).

## Related Tickets

- None

## Related Docs

- `docs/mechanics/`
- `docs/core/state.md`
- `world_phases_0_10_updated.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldbuilding/compiler.py`
- `src/worldbuilding/recipe.py`
- `src/worldbuilding/repository.py`
- `src/world/influence.py`
- `src/engine/world_dynamics.py`

## Assumptions / Open Questions

- None. Phase 0 is purely inventory and architectural boundary freezing.

## Implementation Notes

- We will proceed strictly phase-by-phase. Phase 0 has no functional code changes.

## Test Summary

- We will run existing tests (`pytest tests/ -m "not slow" -x`) to verify that the environment and test suite are in a perfectly healthy, green state.

## Files Changed

- `docs/architecture/world_assembly_architecture.md` (NEW)
- `docs/architecture/world_repository_layout.md` (NEW)
- `staging_artifacts/TCK-20260530-WORLD-PHASE0/hardcoded_inventory.md` (NEW)

## Completion Summary

- To be completed.
