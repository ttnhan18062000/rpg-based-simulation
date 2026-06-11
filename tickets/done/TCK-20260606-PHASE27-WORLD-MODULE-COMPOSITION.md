---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260606-PHASE27-WORLD-MODULE-COMPOSITION
phase: done
date: 2026-06-06
tags: [phase27, world, module, composition]
---

# TCK-20260606-PHASE27-WORLD-MODULE-COMPOSITION

## Title

Phase 27 World Module and Composition Usage Repair

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Prove that real `data/content/world_modules` and `data/content/world_compositions` are executable.

## Scope

- Task 27.1: Add real module integration matrix. Create `tests/integration/worldassembly/test_real_content_world_modules.py` to load, validate, normalize, graph-check, and resolve real modules.
- Task 27.2: Add real composition integration matrix. Create `tests/integration/worldassembly/test_real_content_world_compositions.py` to test composition loading, validation, resolution, assembly, and provenance.
- Task 27.3: Keep provenance deterministic for new paths. Extend/update provenance tests for new module path and archetype/population expansions.

## Out of Scope

- Modifying Phase 28 or Phase 20-26 detailed sections.
- Changing `EntityState` structure.

## Acceptance Criteria

- Real module files are loaded from `data/content/world_modules`.
- Real modules pass schema validation.
- Real modules normalize without structure loss.
- Real modules assemble into contributions.
- Manual injection tests are secondary.
- Real composition file loads.
- `modules` and `module_refs` shortcuts work.
- Output and provenance/fingerprint are deterministic.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldassembly/`
- `tests/integration/worldassembly/`

## Assumptions / Open Questions

- None

## Implementation Notes

- We will write integration tests that load the real files in the repository.
- We will verify that they parse, normalize, and resolve correctly, and verify provenance properties.

- Ran `pytest tests/integration/worldassembly/` and verified all 9 tests pass.
- Verified all unit tests in `tests/unit/worldassembly/` pass.

## Files Changed

- `tests/integration/worldassembly/test_real_content_world_modules.py`
- `tests/integration/worldassembly/test_real_content_world_compositions.py`
- `src/worldassembly/resolver.py`
- `world_phase_20_28_repair.md`

## Completion Summary

- Corrected syntax/indentation errors in `test_real_content_world_modules.py` and proved all real authored world modules load and resolve.
- Implemented `test_real_content_world_compositions.py` to test composition loading, validation, resolution, assembly, determinism, and provenance.
- Updated `WorldAssemblyResolver` to dynamically expand topology dimensions to contain all regions (min_x, min_y, max_x + 1, max_y + 1) when not explicitly specified, avoiding `WORLD-TOPO-001` validation errors.
- Applied `REGION_MIGRATION_MAP` to spawn region resolution for PopulationSpecs to ensure mapped regions (like `trade_road` -> `bandit_road`) are correctly set in compiled WorldSpecs.
- Marked Phase 27 tasks as completed in `world_phase_20_28_repair.md`.
