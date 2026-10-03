---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260410-PHASE-2-ALIGNMENT
artifact_type: test_plan
tags: [phase, alignment]
---

# Test Plan: Phase 2 Alignment Verification

## Automated Tests
- **Strategic Biasing**: `pytest tests/ai/test_strategic_biasing.py`
    - Verifies that strategic objectives correctly bias tactical goal selection (Task 6).
- **Strategic Uncertainty**: `pytest tests/ai/test_strategic_uncertainty.py`
    - Verifies lead and hypothesis logic.
- **Continuity and Interruption**: (New tests needed if not covered)
    - Verify that `project_lock_until` prevents thrashing (Task 3).
    - Verify that high-priority concerns actually interrupt projects (Task 7).

## Manual Verification
- **Inspector Check**:
    - Run the simulation to a certain tick.
    - Use the `EntityInspector` to verify `strategic_drivers` explain the current project/objective.
    - Confirm that `current_project_id` persists across ticks unless interrupted.

## Regression
- Ensure all existing unit tests in `tests/` pass after code refinements.
