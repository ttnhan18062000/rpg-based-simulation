---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION
artifact_type: plan
tags: [simulation-quality, combat]
---

# Plan — TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION

## Steps

1. `tests/simulation_quality/fixtures/grade_anchors.json`: fix the 1 stale, out-of-scope
   NARRATIVE anchor entry surfaced as a side effect (`urban_political_selfmodel_execution_probe_seed42_200t`).
   No change to any COMBAT or the COGNITION anchor (COGNITION already self-resolved via cache
   refresh; COMBAT deliberately left as flagged regressions).
2. `docs/simulation_quality/current_state.md`: append a dated session-summary section documenting
   this disposition (mirrors the existing "2026-08-07 session summary" section's own format).
3. `docs/simulation_quality/eval_matrix_results.md`: append "Anchor Reliability Verification, Part 3"
   following the exact Part 1/Part 2 heading/structure precedent, documenting the F6-hypothesis
   refutation and per-pair disposition.
4. File `TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE` as a new, separate, properly
   registered ticket — the actual engine/scoring root-cause fix is out of this ticket's own scope.
5. No `src/` changes. No `SCORE_TOLERANCE_OVERRIDES` additions.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md reports 3-trial disposition for every flagged pair (or justified representative subset, disclosed) | Full coverage — all 27 unique run_keys, no narrowing needed (methodology proved fast enough: ~13 min for 81 real engine runs) |
| Each pair gets a disposition | 1 no-action (transient), 26 flagged genuine regression (not overridden) |
| test_grade_regression.py -m "not slow" reflects disposition | Passes for the 1 resolved pair; still correctly flags all 26 real regressions |
| current_state.md/eval_matrix_results.md updated, established format | Steps 2-3 |
| Scoped pytest passes | `test_grade_regression.py -m "not slow"` run — 26 pre-existing, disclosed, intentional failures remain (correct outcome, not a broken gate) |
