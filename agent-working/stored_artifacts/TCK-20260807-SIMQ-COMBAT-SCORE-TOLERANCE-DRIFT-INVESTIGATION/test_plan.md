---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION
artifact_type: test_plan
tags: [simulation-quality, combat]
---

# Test Plan — TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION

## Verification

1. `tests/simulation_quality/test_grade_regression.py -m "not slow"` — after the one NARRATIVE
   anchor fix, all remaining failures are exclusively the 26 disclosed, confirmed-stable COMBAT
   regression pairs (24 parametrized + 2 isolated-anchor tests) — no unexplained new failures, no
   accidental new passes masking a real issue.
2. `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[simq_routing_test_seed42_500t]`
   — passes (confirms the 1 transient COGNITION pair correctly resolved without any anchor edit).
3. No `SCORE_TOLERANCE_OVERRIDES` entries added — the 26 COMBAT pairs are deliberately left
   failing as flagged genuine regressions, not laundered into tolerance.

## Anti-drift guard

This ticket does NOT touch `src/engine/kernel.py`'s watchdog/throttle logic (Out of Scope,
explicit). Confirm no `src/` files under `src/engine/` are in `git status --porcelain` from this
ticket's own work.
