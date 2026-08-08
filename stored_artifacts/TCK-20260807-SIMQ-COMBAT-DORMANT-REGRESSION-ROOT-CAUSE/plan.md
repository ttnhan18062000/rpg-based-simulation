---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE
artifact_type: plan
tags: [simulation-quality, combat]
---

# Plan — TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE

## Steps

1. `tests/simulation_quality/fixtures/grade_anchors.json`: recalibrate 26 COMBAT entries to their
   confirmed-stable post-fix values (reusing predecessor ticket's own captured 3-trial data — no
   new engine runs).
2. `docs/simulation_quality/current_state.md`/`eval_matrix_results.md`: close out the disposition.
3. No `src/` changes — root cause already fixed in code (2026-08-06); this ticket is anchor
   recalibration only.
4. Disclose, do not fix, the 1 newly-surfaced COGNITION anchor issue.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies actual root cause with real evidence | Done — 2 already-landed 2026-08-06 changes, confirmed still live in code |
| Fix applied | Anchor recalibration (26 entries), not a code fix — code was already fixed |
| test_grade_regression.py -m "not slow" passes for all 26 previously-flagged pairs | Confirmed |
| docs updated with resolution | Steps 2 |
| Scoped pytest passes | 1 new unrelated failure disclosed, not silently hidden |
