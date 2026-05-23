# Plan - Lab CLI (Milestone 81)

We will design a standalone CLI tool `rpg-lab` to run, monitor, validate, and report on Scenario Lab executions.

## Proposed CLI Design

The CLI entrypoint `src/lab/cli.py` will use `argparse` to declare subcommands with clear help messages:

1. **`validate-world <world_id>`**: Instantiates `WorldRepository` + `WorldValidator`. Validates topologies, bounds, regions, factions, spawning. Returns `0` on success, `1` on failure.
2. **`validate-scenario <scenario_id>`**: Instantiates `ScenarioRepository` + `ScenarioValidator`. Validates against world reference.
3. **`validate-experiment <experiment_id>`**: Instantiates `ExperimentRepository` + `ExperimentValidator`. Validates runs/ticks/seeds/scenario.
4. **`run <experiment_id> [--lab-run-id <id>]`**: Executes orchestrator sequential pipeline. Returns `0` on completed/partial success, `1` on complete failure.
5. **`status <lab_run_id>`**: Retrieves manifest from `LabResultStore`.
6. **`report <lab_run_id>`**: Resolves `lab_summary.md` and prints its location.
7. **`list`**: Resolves index and prints a formatted text table of all run IDs and statuses.
8. **`inspect <lab_run_id>`**: Loads `lab_summary.json` and outputs formatted JSON to stdout.

## Verification Plan

A new suite `tests/cli/test_lab_cli.py` will mock components or use temporary repositories to execute and assert:
- Exit codes for valid/invalid specifications.
- Successful executions creating runs and updating manifests.
- Correct text printing for status, report, list, and inspect commands.
