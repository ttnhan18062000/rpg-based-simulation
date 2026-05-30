# TCK-20260530-PHASE11-ASSEMBLY-HARDENING

## Title

Phase 11 Assembly Hardening and CompileContext Integrity

## Status

DONE

## Request Summary

Implement Phase 11 as specified in the Next Phases Implementation Plan (world_phases_11_19.md). Make explicit profile references survive assembly and populate CompileContext inside ResolvedWorldBundle, split assembly stages, specify module dependency semantics, and fix provenance determinism.

## Scope

- [x] Extend `ResolvedWorldBundle` to include `compile_context: CompileContext`.
- [x] Preserve explicit module population recipe profile references (`stats_profile`, `inventory_profile`, `cognition_profile`) through assembly, making them survive instead of falling back to default roles.
- [x] Decouple `WorldAssemblyResolver` into separate stages: Structural Merger, WorldAssemblyValidator, and CompileProfileResolver.
- [x] Formally document and enforce that `requires` references module IDs for Kahn's topological sort, whereas `provides` serves as descriptive tags.
- [x] Make provenance creation use deterministic `content_fingerprint` while separating `created_at` timestamp in assertions so operational timestamp changes do not break byte-identity checks.

## Out of Scope

- Implementing the custom resolve CLI or lab orchestrator integration (Phase 12).
- Expanding procedural generation or adding runtime registry Bridges (Phases 13–16).

## Acceptance Criteria

- [x] `ResolvedWorldBundle` includes `CompileContext`.
- [x] Explicit module profile references affect compiled entity stats.
- [x] Clean `worldspec.v1` remains unchanged without carrying profile metadata.
- [x] Resolver, validator, and report builders are cleanly separated.
- [x] Module dependency rules are documented and tested.
- [x] Provenance manifest uses deterministic fingerprinting.
- [x] All unit tests pass.

## Related Tickets

- None

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldassembly/resolver.py`
- `src/worldassembly/context.py`
- `src/worldbuilding/compiler.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/unit/worldassembly/test_provenance.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- We modified `ResolvedWorldBundle` to carry the resolved `compile_context` and decoupled the assembly stage into a clean staged pipeline (`WorldAssemblyResolver`, `WorldAssemblyValidator`, `WorldAssemblyReportBuilder`, and `CompileProfileResolver`).

## Test Summary

- Added `test_resolved_bundle_includes_compile_context_and_preserves_profiles` to verify `ResolvedWorldBundle` carries `CompileContext` and preserves explicit population recipe profiles.
- Updated `test_provenance_determinism` to assert deterministic content fingerprints and manifest IDs, stripping operational timestamps before full byte-identical comparisons.
- Run `pytest tests/unit/worldassembly/` - all 7 tests passed successfully.

## Files Changed

- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/unit/worldassembly/test_provenance.py`

## Completion Summary

- Phase 11 has been successfully completed with all acceptance criteria satisfied and fully verified.
