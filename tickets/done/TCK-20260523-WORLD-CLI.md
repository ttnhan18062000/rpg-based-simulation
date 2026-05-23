# TCK-20260523-WORLD-CLI

## Title

Milestone 72 — World CLI / Tooling

## Status

DONE

## Request Summary

Implement a robust, clean command-line interface `rpg-world` to make worldbuilding and procedural template expansion/compilation usable without writing code.

## Scope

- Create a dedicated CLI script `src/worldbuilding/cli.py` with commands:
  - `list`: Lists all worlds in the repository.
  - `validate <world_id>`: Safely validates a world spec, outputting ERROR/WARNING/INFO diagnostics.
  - `compile <world_id> --seed 42`: Compiles a world spec into `AuthoritativeState`, writing a compile report.
  - `inspect <world_id>`: Inspects topological/entity metadata of a world.
  - `create-template <template_name> <world_id>`: Writes a starter/starter template world configuration file to data folders.
- Add `--strict` mode to `compile` and `validate` to treat WARNINGs as failures.
- Map the script to `rpg-world` command inside `pyproject.toml`.
- Write exhaustive CLI unit/integration tests in `tests/cli/test_world_cli.py`.

## Out of Scope

- Live visual UI map visualization in terminal.
- Simulation execution from `rpg-world` CLI (this belongs to `rpg-sim`).

## Acceptance Criteria

- `rpg-world list` prints a formatted table of all available worlds.
- `rpg-world validate` shows detailed rule diagnostics and exits with non-zero code on errors.
- `rpg-world compile` compiles the world safely, generates the json compile report, and respects `--strict` mode.
- `rpg-world inspect` prints summary counts and bounding topologies.
- `rpg-world create-template` creates a valid template world starter configuration.
- 100% passing tests inside `tests/cli/test_world_cli.py`.

## Related Tickets

- `TCK-20260523-WORLD-TEMPLATES`

## Related Docs

- `world_phase11.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldbuilding/cli.py`
- `pyproject.toml`
- `tests/cli/test_world_cli.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Seamlessly integrated with Pydantic custom specs and the newly designed procedural `WorldTemplateSpec` schemas.
- Enhanced `WorldRepository.rebuild_index` to dynamically read and parse procedural templates (`status: TEMPLATE`) in addition to static world specs, making them fully integrated first-class entities in the world registry.

## Test Summary

- 8 new CLI unit/integration test cases implemented in `tests/cli/test_world_cli.py` (all passing).
- Fully validated system integration using standard subprocess and entry point execution.

## Files Changed

- `src/worldbuilding/cli.py`
- `src/worldbuilding/repository.py`
- `pyproject.toml`
- `tests/cli/test_world_cli.py`

## Completion Summary

- Milestone 72 completed with 100% test coverage and full compliance with simulation mechanics and entry point routing constraints.
