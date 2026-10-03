---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260523-LAB-CLI
phase: done
date: 2026-05-23
tags: [lab, cli]
---

# TCK-20260523-LAB-CLI

## Title

Milestone 81 — Lab CLI / Tooling

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Create the standalone `rpg-lab` CLI (Milestone 81) providing operators with the ability to validate specs, execute sweeps, check status, inspect results, and generate markdown reports directly from the terminal.

## Scope

- Create a new CLI entrypoint in `src/lab/cli.py` with subcommands:
  - `validate-world <world_id>`
  - `validate-scenario <scenario_id>`
  - `validate-experiment <experiment_id>`
  - `run <experiment_id> [--lab-run-id <id>]`
  - `status <lab_run_id>`
  - `report <lab_run_id>`
  - `list`
  - `inspect <lab_run_id>`
- Register `rpg-lab` CLI script in `pyproject.toml`.
- Implement tests in `tests/cli/test_lab_cli.py` covering all CLI subcommands.

## Out of Scope

- Real-time curses/TUI web dashboard in CLI.
- Execution budgets pre-flight warnings (Milestone 82).

## Acceptance Criteria

- [x] `rpg-lab` CLI command is registered and executable.
- [x] Spec validations (`validate-world`, `validate-scenario`, `validate-experiment`) return zero on success and non-zero on validation failures.
- [x] `run` executes the orchestrator correctly, creating isolated directories and writing summaries.
- [x] `status` prints correct status, run progress, and metrics.
- [x] `report` prints the human-readable markdown scorecard path and details.
- [x] `list` lists executed lab runs in an aligned table layout.
- [x] `inspect` outputs formatted JSON of the lab summary.
- [x] CLI tests are passing successfully.

## Related Tickets

- `TCK-20260523-LAB-RESULT-STORE`

## Related Docs

- `lab_phase12.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/cli.py`
- `pyproject.toml`
- `tests/cli/test_lab_cli.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented safe pydantic exception validation formatting inside CLI command routes.
- Fully registered and verified packaging entrypoints using subprocesses.

## Test Summary

- All 7 tests in `test_lab_cli.py` passed successfully.
- Total CLI suite of 30 tests fully passing.

## Files Changed

- `src/lab/cli.py`
- `pyproject.toml`
- `tests/cli/test_lab_cli.py`

## Completion Summary

- Delivered a robust standalone CLI tool `rpg-lab` integrating all specification validations and sweep execution controls with isolated repo directory support.
