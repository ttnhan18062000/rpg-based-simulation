---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE

## No fix lands in this ticket
`investigation.md` identifies 2 real, plausible, non-exclusive contributing factors (tactical-
evaluation cadence-gating starving initial hostile detection; `find_intercept_position`'s
prediction potentially diverging against a non-combat-aware wandering target) but real chase
volume in the corpus (11/2 total decisions across 4000 combined ticks) is too sparse to
conclusively attribute the observed non-convergence to either factor alone via black-box corpus
probing. Per the Uncertainty Rule ("do not collapse investigation into exact coordinates too
early") and this session's own established precedent
(`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`), this ticket closes as
investigation-plus-recommendation rather than forcing a speculative fix.

## Recommendation: dedicated per-tick trace, not corpus-wide sampling
The next real step is qualitatively different from this ticket's own methodology: instead of
sampling tactical-*decision* ticks across the whole corpus (sparse, ~1 decision per ~180-2000
ticks per entity), a follow-up should track one real, hand-selected pursuing entity's
`navigation.target` / `movement_mode` / real distance-to-target on **every** tick of a live
5.0-10-tick chase window (not just its own tactical-decision ticks), to distinguish:
1. Cadence starvation: the entity's `navigation.target`/`movement_mode` stays stale (unchanged)
   for multiple ticks in a row because `execute_brain()`'s cadence gate skips re-evaluation —
   confirms Finding 2 as load-bearing.
2. Intercept-prediction divergence: `navigation.target` changes every tactical-decision tick, but
   each new prediction is *worse* (farther from the target's real position) than the last —
   confirms Finding 3 as load-bearing.
Filed as `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (investigation-first, standard tier).

## Rejected alternative
- **Speculatively raising `SystemCadence.strategic_intelligence` or reworking
  `find_intercept_position` now**: rejected — changing either without confirming which (if
  either) is load-bearing risks a real regression-for-no-confirmed-benefit outcome, the same
  risk class this session's own `TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES` ticket
  explicitly avoided for an analogous reason.

## Verification plan
N/A — no code change in this ticket. The follow-up ticket's own verification plan will cover the
per-tick trace methodology described above.
