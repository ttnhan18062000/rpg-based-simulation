# Investigation: World CLI / Tooling

We want to introduce a standalone command `rpg-world` that operates as a CLI tool for file-based world building.

## Requirements from `world_phase11.md`

1.  **Commands**:
    *   `rpg-world list`: Lists all worlds from the repository (reading index and directory).
    *   `rpg-world validate <world_id>`: Safely validates a world spec, outputting ERROR/WARNING/INFO rules.
    *   `rpg-world compile <world_id> --seed 42`: Refuses compile on ERROR, writes `world_compile_report.json` on success.
    *   `rpg-world inspect <world_id>`: Prints summary counts and dimensions.
    *   `rpg-world create-template <template_name> <world_id>`: Writes a starter/boilerplate template.

2.  **Flags & Behavior**:
    *   `--strict`: In `compile` and `validate`, treats warnings as errors (failure / non-zero exit code).
    *   `--seed`: Compiles deterministically.

## Design Choices

*   Use `argparse` for standard CLI parsing. It is already standard in the codebase (`src/cli/entry.py`).
*   Output text formatting: Use standard formatted terminal outputs. Keep it extremely legible, neat, and structured.
*   Integrating template creation: `create-template` should write a beautiful starter YAML template including sample topology, a region, faction, population recipe, resource recipe, and building recipe.
