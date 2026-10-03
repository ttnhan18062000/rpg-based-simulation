---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP
artifact_type: test_plan
tags: [cognition, observability, simulation-quality]
---

# test_plan.md — TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP

## Regression Surface (existing tests that must pass)

- `tests/unit/observability/cognition/test_cognition_capture_policy.py` — all existing tests must
  still pass (verified: 4/4 before this ticket's change).
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` — SimQ's calibration harness
  observability mode is unchanged by this ticket's recommendation, so no anchor impact expected.

## New Tests Required (per AC)

- `test_normal_full_research_modes_capture_state_changes` (parametrized over NORMAL/FULL/RESEARCH)
  added to `test_cognition_capture_policy.py`, mirroring the existing `test_debug_mode_captures_all_reasons`
  pattern.

## Scoped Pytest Commands

```
pytest tests/unit/observability/cognition/test_cognition_capture_policy.py -v
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

## Anti-Drift Test Guards

The new parametrized test explicitly asserts both the "captures selected entity" and "does not
capture unselected entity for non-anomaly reasons" branches for each of NORMAL/FULL/RESEARCH —
guards against a future regression silently narrowing capture back to DEBUG/CERTIFICATION-only.
