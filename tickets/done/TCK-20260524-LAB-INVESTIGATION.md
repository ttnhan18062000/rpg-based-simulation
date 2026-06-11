---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260524-LAB-INVESTIGATION
phase: done
date: 2026-05-24
tags: [lab, investigation]
---

# TCK-20260524-LAB-INVESTIGATION

## Title

Implement InvestigateSimulationResult Workflow (Milestone 100)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the `InvestigateSimulationResultWorkflow` in `src/lab/workflows.py` to analyze registered and compacted simulation run data at different analysis depths (light, standard, deep) and write structured investigation reports and backlogs.

## Scope

- Create `InvestigateSimulationResultWorkflow` class in `src/lab/workflows.py`
  - Load the compaction artifacts from the active lab session.
  - Implement three depth analysis modes:
    - **Light**: Read summary, issue index, and top 3 issues.
    - **Standard**: Read summary, issue index, top 10 issues, top evidence packs, signal coverage, and known issues.
    - **Deep**: Read standard data, selected event windows, selected metric windows, and cognition/entity evidence.
  - Enforce O(1) performance rules and token safety limits (raw log files must NOT be fully loaded into memory or tokens).
  - Generate the 6 output artifacts under `investigation/` session directory:
    1. `investigation_report.md`
    2. `investigation_report.json`
    3. `issue_backlog.json`
    4. `missing_signals.json`
    5. `insight_candidates.json`
    6. `next_experiment_suggestions.json`
- Apply safe path resolution and sandbox guards to block traversal breakouts.
- Export `InvestigateSimulationResultWorkflow` in `src/lab/__init__.py`.
- Write integration tests inside `tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`.

## Out of Scope

- Implementing `ProposeSimulationEnhancementsWorkflow` (M101).
- Direct visualization rendering on frontend pages.

## Acceptance Criteria

- Three levels of analysis depths (light, standard, deep) are supported and behave exactly as specified.
- The 6 output investigation files are successfully written to `data/lab_sessions/{session_id}/investigation/`.
- Paths are validated with `safe_path_resolution()` to prevent sandbox escapes.
- Massive raw files are NOT fully loaded or read in memory.
- Integration tests cover all required cases (light/standard/deep mode assertions, backlog creation, missing signals, invalid state blocking).

## Related Tickets

- `TCK-20260524-LAB-COMPACT-SIMULATION` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260524-LAB-COMPACT-SIMULATION/`

## Related Code Areas

- `src/lab/workflows.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Designed `InvestigateSimulationResultWorkflow` to dynamically classify rule violations into standard domain groups (movement, resource, combat, strategy, kernel).
- Constructed premium user scorecard in markdown conforming exactly to the 13 required structural sections.

## Test Summary

- Run `pytest tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`. All 5 tests passed successfully in 0.28 seconds.
  - Covers Light analysis depth (top 3 issue counts).
  - Covers Standard analysis depth (top 10 issue counts + coverage gaps).
  - Covers Deep analysis depth (prioritized issues + experiment suggestions).
  - Covers block triggers on FAILED/unsupported lab run states.
  - Covers traversal escape blocked validations raising PermissionError.

## Files Changed

- `src/lab/workflows.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`

## Completion Summary

- Milestone 100 (M100) is fully complete. All artifacts are verified and compiled.
