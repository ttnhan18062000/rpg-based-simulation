# Plan: World CLI / Tooling

We will create a clean and decoupled command-line interface under `src/worldbuilding/cli.py`.

## Subcommands Implementation

1.  **`list`**:
    *   Initialize `WorldRepository()`.
    *   Fetch available worlds and format them as an ASCII/formatted tabular list.
    *   Print tagging, health status, and metadata.

2.  **`validate`**:
    *   Load target world from repo.
    *   Run `WorldValidator`.
    *   Print each diagnostic message colorfully with its severity and rule ID.
    *   If strict is set and there are warnings, or if there are errors, exit with code `1`. Otherwise `0`.

3.  **`compile`**:
    *   Load target world.
    *   Perform compile via `WorldCompiler.compile`.
    *   Save compile report JSON.
    *   Handle warnings appropriately. Respect `--strict`.

4.  **`inspect`**:
    *   Show detailed overview of the spec (number of regions, factions, resource nodes, buildings, entities).

5.  **`create-template`**:
    *   Generate a baseline starter world spec or starter recipe template YAML.
    *   Save to the repo directory under the provided `world_id`.

## Integration

*   Register script `rpg-world` in `pyproject.tomlproject.scripts`.
