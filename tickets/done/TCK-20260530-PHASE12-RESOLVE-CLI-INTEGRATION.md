# TCK-20260530-PHASE12-RESOLVE-CLI-INTEGRATION

## Title

Phase 12 — Resolve CLI, Artifact Contract, and Lab Integration

## Status

DONE

## Request Summary

Implement Phase 12 as specified in `world_phases_11_19.md`. Create a first-class resolve command in `rpg-world` CLI, export resolved bundle artifacts to disk following the standardized contract, allow `compile` to load and consume `compile_context.json`, and make lab execution aware of resolved world artifacts.

## Scope

- [x] Add `resolve` subcommand to `rpg-world` CLI in `src/worldbuilding/cli.py`.
- [x] Implement `handle_resolve` to load `worldcomposition.v1` compositions, run topological sorted merging, validation, and write standard resolved artifacts:
  - `data/worlds/<world_id>/resolved/world.resolved.yaml`
  - `data/worlds/<world_id>/resolved/compile_context.json`
  - `data/worlds/<world_id>/resolved/provenance_manifest.json`
  - `data/worlds/<world_id>/resolved/assembly_report.json`
  - `data/worlds/<world_id>/resolved/validation_report.json`
- [x] Modify `compile` subcommand / `handle_compile` to automatically detect or support `--from-resolved` mode, loading `world.resolved.yaml` along with `compile_context.json` and passing the context to `WorldCompiler.compile(world_spec, context=compile_context)`.
- [x] Support JSON serialization and deserialization of `CompileContext`.

## Out of Scope

- Implementing the runtime catalog expansion (Phase 13).
- Seed phase runtime bridges (Phase 15).

## Acceptance Criteria

- [x] `rpg-world resolve <world_id>` command works and writes the full contract of 5 files to disk under `<world_dir>/resolved/`.
- [x] `rpg-world compile <world_id>` detects composition worlds, loads `compile_context.json` and compiles them with full context.
- [x] Missing `compile_context.json` for a composition raises a controlled compile error unless `--legacy-fallback` is specified.
- [x] Unit tests verify the serialization/deserialization of `CompileContext` and resolve CLI command.

## Related Tickets

- `TCK-20260530-PHASE11-ASSEMBLY-HARDENING`

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldbuilding/cli.py`
- `src/worldassembly/context.py`
- `src/worldbuilding/repository.py`
- `tests/unit/worldassembly/`

## Assumptions / Open Questions

- None

## Implementation Notes

- We implemented `to_dict` and `from_dict` methods inside `CompileContext` for seamless JSON marshalling.
- Added `handle_resolve` to `src/worldbuilding/cli.py` and modified `handle_compile` to cleanly load resolved specifications and compile contexts before triggering compilation.

## Test Summary

- Added `test_compile_context_serialization` verifying correct serialization/deserialization of `CompileContext`.
- Added `test_cli_resolve_and_compile_integration` programmatically validating CLI command dispatches and safe file generation.
- Run `pytest tests/unit/worldassembly/` - all 9 tests passed.

## Files Changed

- `src/worldassembly/context.py`
- `src/worldbuilding/cli.py`
- `tests/unit/worldassembly/test_assembly.py`

## Completion Summary

- Phase 12 resolve CLI integration has been successfully implemented and verified.
