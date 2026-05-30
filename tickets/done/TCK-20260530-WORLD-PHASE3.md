# TCK-20260530-WORLD-PHASE3

## Title

World Data Refactor Phase 3: Profile Consumer Bridge

## Status

DONE

## Request Summary

Implement the Profile Consumer Bridge. Create the `CompileProfileResolver` inside `src/worldassembly` to translate and resolve static recipes, role, and faction references into compiler-ready profiles. Wire this profile resolver into the `WorldCompiler` through a new optional `CompileContext` object, allowing profile-backed settings to govern compile attributes (e.g. entity HP/atk, starting gold, node tick-cost) while fully preserving backward compatibility for old world specifications.

## Scope

- Define internal normalized resolved models for entity, building, resource, and faction economy profiles in `src/worldassembly/models.py`.
- Create `CompileProfileResolver` under `src/worldassembly/resolver.py` that merges explicit profile overrides, role/faction defaults, and global defaults.
- Create `CompileContext` under `src/worldassembly/context.py` to hold resolved profiles.
- Refactor the compiler `WorldCompiler.compile` in `src/worldbuilding/compiler.py` to accept `CompileContext` and override hardcoded default parameters using resolved profiles.
- Run the full worldbuilding test suite to prove zero regression on legacy templates or specs.

## Out of Scope

- Implementing the structural module resolution system or layout composition.
- Creating the world compiler validation pipeline changes before Phase 5.

## Acceptance Criteria

- [x] Internal normalized profile models exist in `src/worldassembly/models.py`.
- [x] `CompileProfileResolver` implemented in `src/worldassembly/resolver.py` resolving with catalog-backing and proper fallbacks.
- [x] `CompileContext` holds resolved profile lookups.
- [x] `WorldCompiler.compile` correctly overrides hardcoded default values with values supplied by the resolved context.
- [x] Backward compatibility: worlds compiled without `CompileContext` produce identical legacy defaults.
- [x] Unit tests cover custom stats, default overrides, missing profile reference errors, and building service profile resolution.
- [x] No regressions in existing simulation or scenario tests.

## Related Tickets

- `TCK-20260530-WORLD-PHASE2`

## Related Docs

- `docs/architecture/world_assembly_architecture.md`
- `world_phases_0_10_updated.md`

## Related Code Areas

- `src/worldassembly/models.py`
- `src/worldassembly/resolver.py`
- `src/worldassembly/context.py`
- `src/worldbuilding/compiler.py`

## Assumptions / Open Questions

- None.

## Test Summary

- We will write comprehensive unit tests under `tests/unit/worldassembly/` to verify resolution behavior and compiler integration.

## Files Changed

- `src/worldassembly/models.py` (NEW)
- `src/worldassembly/resolver.py` (NEW)
- `src/worldassembly/context.py` (NEW)
- `src/worldbuilding/compiler.py` (MODIFY)
