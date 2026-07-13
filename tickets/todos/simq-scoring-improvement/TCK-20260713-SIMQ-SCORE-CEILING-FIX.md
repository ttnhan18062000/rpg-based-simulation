---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-SCORE-CEILING-FIX
phase: open
date: 2026-07-13
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260713-SIMQ-SCORE-CEILING-FIX

## Title
Recalibrate the weight/normalization scale for WORLD, ECONOMY, PROGRESSION, INFORMATION — these
4 pillars structurally cannot reach grade A or S under any real-world condition

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Prompted by a direct question about whether SimQ's scoring multipliers need adjustment (not just
corpus coverage). Cross-referencing raw `normalized_score` values (from a full live corpus run,
`tmp/evaluate_simq_full_run_20260713.log`, session-local) against the grade-band thresholds
(`quality_scoring_contract.md` §4.5: `S >2.0`, `A 0.5-2.0`, `B 0.0-0.5`) across all 72 committed
anchor scenarios found that 4 of SimQ's 10 pillars structurally cannot reach A or S under the
current weight scale, regardless of how good the underlying world is:

| Pillar | Max normalized score seen (all 72 scenarios) | A threshold | Gap |
|---|---|---|---|
| WORLD | 0.30 (a 38-event run) | 0.5 | Never halfway there — the pillar's entire observed range (0.0-0.3) fits inside the B band alone |
| ECONOMY | 0.16 (a **69-event** run — genuinely rich activity) | 0.5 | 1/3 of the way even at its richest observed point |
| PROGRESSION | 0.13 (46-event run) | 0.5 | Same shape |
| INFORMATION | 0.04 (1-event run) | 0.5 | ~12x short |

This is a weight/normalization-scale problem, not a corpus-coverage problem: even the single
richest ECONOMY run in the whole corpus (69 scored events) only reached 1/3 of the way to A. The
scorer currently cannot ever register a world as *exceptional* on these 4 dimensions — a real gap
against SimQ's own stated balance/tuning-support goal (`quality_scoring_contract.md` §1), which
needs the top of the scale to be reachable to be useful. By contrast, NARRATIVE and COMBAT (the
other two "always-on", non-gated pillars) show real spread across all 4 grades and are not
exhibiting this pattern — confirming this is specific to these 4 pillars' weight/threshold
calibration, not a property of the normalization formula itself.

## Scope
- Investigate each affected pillar's scorer (`src/simulation_quality/scorers/world_dynamics.py`,
  `economy.py`, `progression.py`, `information.py`) and its weights
  (`config/simulation_quality/scoring_weights.yaml`) to understand exactly why per-event deltas
  are scaled so low relative to the `normalized_score` formula's denominator
  (`quality_scoring_contract.md` §4.4).
- Deliberately construct or identify one genuinely best-case and one genuinely worst-case scenario
  per affected pillar within the existing corpus (or a new minimal test scenario if none exists),
  run them through the current formula, and determine whether raising per-event weights, lowering
  grade thresholds for these 4 pillars specifically, or both, restores real discrimination.
- Re-anchor `grade_anchors.json` for whichever entries actually change under the corrected formula
  — full regression sweep required, since shared weight constants can move grades corpus-wide.

## Out of Scope
- ECONOMY's Gini-threshold mechanism itself, or COMBAT/NARRATIVE's formulas — these are not
  exhibiting the same ceiling pattern; not touched unless investigation finds otherwise.
- Authoring new content into any world — that's `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`, which
  depends on this ticket landing first.
- The `grade_anchors.json` schema extension for raw-score persistence
  (`TCK-20260713-SIMQ-RAWSCORE-PERSIST`) — sequenced to reuse this ticket's re-anchor pass, but is
  its own separate concern (schema/regression-test change, not a weight-formula change).
- Any of `quality_scoring_contract.md` §14's Non-Goals.

## Acceptance Criteria
- [ ] For each of the 4 affected pillars, at least one real corpus scenario reaches grade A or S
      under the recalibrated formula.
- [ ] Structurally-inert entries (e.g. INFORMATION in worlds with zero information content, or
      ECONOMY in worlds with no harvest/craft/trade activity) remain C — the fix must move the
      ceiling for genuinely active scenarios, not just inflate every score uniformly.
- [ ] Full `evaluate_simq.py` (live mode) sweep shows 0 unattributed regressions — every anchor
      change is a deliberate, documented consequence of the weight/threshold change, not a side
      effect.
- [ ] `docs/simulation_quality/current_state.md`'s grade-distribution table and discriminative-
      power section are updated to reflect the new, corrected state.

## Related Tickets
- `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` — depends on this ticket landing first.
- `TCK-20260713-SIMQ-RAWSCORE-PERSIST` — sequenced to share this ticket's re-anchor pass.
- `TCK-20260713-SIMQ-EVAL-PROFILE-BUG` — should land first so this ticket's repeated live-mode
  sweeps (while tuning weights) aren't run against a tool with a known silent-corruption bug.

## Related Docs
- `docs/simulation_quality/current_state.md` — the discriminative-power finding this ticket
  addresses, with the full evidence table.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 1a, this ticket's source.
- `docs/simulation_quality/quality_scoring_contract.md` §4.4 (normalized score formula), §4.5
  (grade bands), §1 (goals — balance/tuning support).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `config/simulation_quality/scoring_weights.yaml`
- `src/simulation_quality/scorers/world_dynamics.py`
- `src/simulation_quality/scorers/economy.py`
- `src/simulation_quality/scorers/progression.py`
- `src/simulation_quality/scorers/information.py`
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` (`_within_band`, `GRADE_ORDER`, line ~34/140)

## Assumptions / Open Questions
- Whether the fix should be "raise weights" or "lower thresholds" (or both, per-pillar
  differently) is explicitly left to the implementer's investigation — the roadmap and this
  ticket deliberately do not pre-decide this, since it requires empirical construction of best/
  worst-case scenarios that hasn't been done yet.
- The exact best-case/worst-case scenarios to construct per pillar are not yet identified — first
  investigation task.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
