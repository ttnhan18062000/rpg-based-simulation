# TCK-20260530-WORLD-PHASE5

## Title

World Data Refactor Phase 5: WorldCompositionSpec and Structural Assembly Resolver

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish the Composition and Assembly Resolver pipeline. Define pydantic schema `WorldCompositionSpec` allowing world scenarios to reference catalogs and modules, load them recursively, perform deterministic top-down module sorting, merge modular layout fragment lists safely, evaluate parameter specifications, and generate a clean `ResolvedWorldBundle` containing a validated `worldspec.v1` and sidecar provenance/assembly logs.

## Scope

- Define Pydantic schema for `WorldCompositionSpec` under `src/worldassembly/schema.py`.
- Implement `WorldAssemblyResolver` under `src/worldassembly/resolver.py` taking care of topological sort execution, parameters evaluation, merging recipes, resolving default profiles, and spitting out `ResolvedWorldBundle` objects.
- Ensure that the resulting `WorldSpec` has no dynamic metadata fields (such as `source_module_id`) inside the compiled entity models (these are sidecarred strictly in `ProvenanceManifest`).
- Expand `WorldRepository` to recognize `worldcomposition.v1` scenarios in `src/worldbuilding/repository.py`.
- Implement tests verifying structural assembly resolution and backwards compatibility for existing templates/specs.

## Out of Scope

- upgrading validation to Scoped context enums (this belongs to Phase 6).
- Procedural generation algorithms or triggers.

## Acceptance Criteria

- [x] `WorldCompositionSpec` schema defined and validated.
- [x] `WorldAssemblyResolver` successfully parses, merges, and validates modules topologically.
- [x] `CompileProfileResolver` called during assembly to enrich profiles.
- [x] Provenance sidecar manifest contains structural fingerprints and source origins.
- [x] Assembly resolves a fully clean `worldspec.v1` spec object.
- [x] `WorldRepository` registers and indexes `worldcomposition.v1` successfully.
- [x] Tests cover deterministic ties, parameter checking, circular graphs detection, and compilation compatibility.
- [x] No regression on existing templates or compiler tests.

## Related Tickets

- `TCK-20260530-WORLD-PHASE4`

## Related Docs

- `docs/architecture/world_assembly_architecture.md`
- `docs/architecture/world_repository_layout.md`
- `world_phases_0_10_updated.md`

## Related Code Areas

- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `src/worldbuilding/repository.py`

## Assumptions / Open Questions

- We will only run structural validation in Phase 5.

## Test Summary

- We will write comprehensive assembly tests under `tests/unit/worldassembly/test_assembly.py`. All tests successfully passed.

## Files Changed

- `src/worldassembly/schema.py` (NEW)
- `src/worldassembly/resolver.py` (MODIFY)
- `src/worldbuilding/repository.py` (MODIFY)
- `tests/unit/worldassembly/test_assembly.py` (NEW)
