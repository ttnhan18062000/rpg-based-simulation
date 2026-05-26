# Plan - Resource, Storage, and Runtime Guardrails (Milestone 82)

Prevent lab executions from accidentally generating excessive computational work, massive artifact storage footprint, or prolonged execution runtimes. 

## Proposed Changes

### Core Schema Updates
* Add optional budget limit fields to `ExperimentBudgetsSpec`:
  * `max_runs`: `Optional[int] = 100`
  * `max_total_ticks`: `Optional[int] = 1000000`
  * `max_parallel_runs`: `Optional[int] = 4`

### Budget Guardrail Implementation
* Create budget exceptions: `BudgetBlockedError` and `BudgetWarningError`.
* Define `BudgetEstimation` container with estimated values for:
  * `run_count`
  * `total_ticks`
  * `expected_entity_count`
  * `expected_event_volume`
  * `expected_artifact_mb`
  * `expected_runtime_minutes`
* Define `BudgetCheckResult` representing `OK`, `WARNING`, or `BLOCKED` status.
* Implement `LabBudgetGuardrails` with profile constraints (`CI` vs `local_dev`).

### Orchestrator Integration
* Enhance `run_lab(..., profile="local_dev", force=False, confirm=False)` to execute checks before creating manifest/directories.
* Write `budget_warnings` to finalized `lab_summary.json` and print them in `lab_summary.md` scorecard.

### CLI Enhancements
* Add `--force` and `--confirm` options to `rpg-lab run` command.
* Catch budget exceptions and print actionable guidance to stderr.
