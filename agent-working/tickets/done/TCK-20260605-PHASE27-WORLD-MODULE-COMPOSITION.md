---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION
phase: done
date: 2026-06-05
tags: [phase27, world, module, composition]
---

# TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION

## Title

World module and composition usage correction

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Make modules and compositions consume lower-layer data properly.
- Task 27.1: Add `ResolvedModuleContribution`
- Task 27.2: Add `WorldCompositionNormalizer`
- Task 27.3: Keep provenance deterministic

## Scope

- Implement `ResolvedModuleContribution` in `src/worldassembly/resolver.py` or new file, which normalizes module v1/v2 data.
- Ensure the resolver calls component resolvers (`PopulationRecipeResolver`, `EcologyResolver`, `RegionResolver`, `ResourceResolver`, `BuildingResolver`, `RelationshipResolver`).
- Implement `WorldCompositionNormalizer` supporting both `module_refs` and `modules` (shorthand list) formats. Preserving `default_perspectives`. Fail on mixed format / unknown fields.
- Make composition fingerprint and provenance deterministic.
- Write tests extending `test_structural_world_assembly_resolver` and composition tests.

## Out of Scope

- Modifying non-assembly subsystems.
- Moving to Phase 28 yet.

## Acceptance Criteria

- `ResolvedModuleContribution` normalizes v1/v2 modules correctly without defining primitive data inline.
- Module refs resolve through component resolvers.
- Duplicate region collision still fails.
- `NormalizedWorldComposition` exists and normalizes both composition input formats.
- Mixed authoring formats fail validation.
- Default perspectives survive normalization.
- Composition fingerprint is deterministic.
- Resolver receives one normalized format only.
- Validation checks pass.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldassembly/resolver.py`
- `src/worldassembly/schema.py`
- `tests/unit/worldassembly/test_assembly.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Normalized composition structures via `NormalizedWorldComposition` to forbid unknown fields.
- Utilized component resolvers at the module resolution step.
- Built heuristics to resolve v2 resource and building placement in regions.
- Calculated a deterministic composition fingerprint hash.

## Test Summary

- Added unit and integration tests to `tests/unit/worldassembly/test_assembly.py`:
  - `test_composition_normalization_shorthand_and_mixed`
  - `test_v2_module_resolution_and_heuristics`
- All 19 assembly/provenance/resolver tests passed.

## Files Changed

- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `tests/unit/worldassembly/test_assembly.py`

## Completion Summary

- Implemented all tasks for Phase 27. Normalization and validation are now fail-closed and robust, and v2 module contributions are fully resolved and assembled deterministically.
