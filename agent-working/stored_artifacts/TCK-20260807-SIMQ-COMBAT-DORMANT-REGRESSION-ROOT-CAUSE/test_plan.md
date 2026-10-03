---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE
artifact_type: test_plan
tags: [simulation-quality, combat]
---

# Test Plan — TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE

## Verification

1. `tests/simulation_quality/test_grade_regression.py -m "not slow"` — all 26 previously-flagged
   COMBAT pairs pass after recalibration. The 1 newly-surfaced, unrelated COGNITION failure
   (`hero_guild_routing_seed42_500t`) is left failing, disclosed, out of this ticket's own scope.
2. No `src/` changes (this ticket is anchor-data-only, per its own confirmed root cause — the code
   fix already landed in `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`).
3. `git status --porcelain -- src/engine/` empty (anti-drift guard, matches predecessor ticket).
