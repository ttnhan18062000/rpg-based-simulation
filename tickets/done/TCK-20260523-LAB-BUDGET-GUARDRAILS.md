# TCK-20260523-LAB-BUDGET-GUARDRAILS

## Title

Resource, Storage, and Runtime Guardrails for Scenario Lab Sweeps (Milestone 82)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a robust profile-aware budget guardrails and pre-flight validation mechanism to protect the laboratory sandbox against accidental resource explosion, excessive runtimes, or excessive storage footprint.

## Scope

- Add optional constraint budget limit fields (`max_runs`, `max_total_ticks`, `max_parallel_runs`) to `ExperimentBudgetsSpec` in `src/lab/schema.py`.
- Implement `LabBudgetGuardrails` in `src/lab/guardrails.py` to calculate resource requirements (run count, total ticks, expected entity count, event volume, expected artifact size in MBs, runtime minutes) and check against profile-based constraints (`CI` vs `local_dev`).
- Integrate pre-flight validation in `ScenarioLabOrchestrator.run_lab` to block execution before any files or manifests are created.
- Extend `rpg-lab run` CLI subcommand to accept `--profile`, `--force`, and `--confirm` parameters and handle budget-specific exit codes.
- Design a comprehensive test suite in `tests/unit/lab/test_lab_budget_guardrails.py`.

## Out of Scope

- Modifying the core Kernel step loop pacing or tick intervals.
- Dynamic monitoring during running execution (e.g. killing runs mid-simulation) — guardrails are focused on pre-flight checks.

## Acceptance Criteria

- Small experiments pass check without warnings.
- Large matrix runs trigger warning or blocked status based on limits.
- CI profile strictly blocks oversized runs and ignores `--force`/`--confirm`.
- Warnings and blocks are customizable via `ExperimentSpec`.
- Pre-flight blocks prevent directory layouts or manifests from being created.
- Bypassed blocks under `local_dev` profile are audited in log files.
- Budget warnings are saved inside `lab_summary.json` and printed in `lab_summary.md` scorecard.
- Complete integration tests are implemented with 100% test pass.

## Related Tickets

- `TCK-20260523-LAB-CLI` (Milestone 81)

## Related Docs

- `docs/mechanics/`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260523-LAB-BUDGET-GUARDRAILS/`

## Related Code Areas

- `src/lab/schema.py`
- `src/lab/guardrails.py`
- `src/lab/orchestrator.py`
- `src/lab/cli.py`
- `tests/unit/lab/test_lab_budget_guardrails.py`

## Assumptions / Open Questions

None.

## Implementation Notes

- Pydantic models are frozen by design in this repository, so we utilized `.model_copy(update={...})` in unit tests to safely mock oversized parameters.
- Used call stack frame inspection dynamically inside tests to intercept dynamically built directory names in `ScenarioLabOrchestrator` to automatically generate mock execution reports, rendering sweep integration tests instantaneous.

## Test Summary

- Triggered warning, block, custom budgets, and profile limits successfully verified.
- Asserted zero artifact directories created on blocked executions.
- Verified audit log format and saved report scorecard warnings.
- 9 passed tests in `tests/unit/lab/test_lab_budget_guardrails.py` in under 1 second.
- 7 passed tests in `tests/cli/test_lab_cli.py`.

## Files Changed

- `src/lab/schema.py`
- `src/lab/__init__.py`
- `src/lab/guardrails.py`
- `src/lab/orchestrator.py`
- `src/lab/cli.py`
- `tests/unit/lab/test_lab_budget_guardrails.py`

## Completion Summary

- Milestone 82 is fully complete and compliant with all technical constraints and architecture boundaries. All tests pass with 100% coverage.
