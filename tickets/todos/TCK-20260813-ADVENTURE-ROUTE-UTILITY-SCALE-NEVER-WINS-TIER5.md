---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5
phase: open
date: 2026-08-13
tags: [adventure, agency, strategy, cognition]
---

# TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5

## Title
`ADVENTURE_ROUTE`'s utility score (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, observed ~20-26
on the shared 0-100 scale) never outscores `COMBAT_ENGAGE`/`REGION_STABILIZATION` in any sampled
seed — adventure routing is structurally dead in tier-5 goal competition, not just an observability
gap

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`'s required AC3
verification step (a fresh `tools/calibrate_simq.py` run against all 6 named run_keys post-fix).
See that ticket's `Implementation Notes` and
`stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/plan.md`'s Deviations
section for full technical detail already gathered — this ticket should read those first rather
than re-deriving from scratch.

That ticket genuinely fixed a real write-path bug: `last_routing_family`/`last_routing_tick` are
now correctly threaded from a winning `ADVENTURE_ROUTE` candidate through to a committed
`EntityUpdate`, verified end-to-end at the unit/integration level (including a direct test that
`StrategyShaper.shape()` emits `route_selected`/`action_executed`/`route_family_first_use` for such
an update).

Despite that fix, `route_selected`/`action_executed`/`route_family_first_use` still measure **0**
events in a fresh calibration run against `simq_routing_test`/`hero_guild_routing` × seeds
{42,123,456} `_500t` — because a winning `ADVENTURE_ROUTE` candidate essentially never occurs in
these worlds' actual 500-tick runs. DEBUG-level tracing of `evaluate_strategic_intent()`'s own
tier-5 goal-selection log across full runs of both worlds, at every sampled seed, found
`ADVENTURE_ROUTE`'s utility (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` on the shared 0-100
competition scale, observed ~20-26 in practice) never once outscores `COMBAT_ENGAGE` (observed
~100-144) or `REGION_STABILIZATION` (observed flat 100.0) — one or the other is active on
effectively every evaluated tick for every hero entity in both worlds.

This is a distinct, deeper problem than the write-path bug the originating ticket fixed: even with
observability restored, `ADVENTURE_ROUTE` is structurally unable to win tier-5 arbitration in these
worlds' current configuration, which plausibly traces to
`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s architecture change — before that ticket,
`AdventureDecisionPhase` ran as an unconditional standalone phase (never competing against other
`GoalKind`s at all); after, `ADVENTURE_ROUTE` competes as an ordinary tier-5 `GoalScorer` candidate
on a scale apparently never calibrated against the other scorers' typical output ranges.

## Scope
- Determine, with real evidence (not assumed), whether `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` and/or
  `AdventureGoalScorer`'s own scoring formula were ever calibrated against the 0-100 shared
  tier-5 competition scale other `GoalScorer`s use, or whether this is an unnoticed unit/scale
  mismatch introduced by `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s architecture change.
- Determine whether `COMBAT_ENGAGE`'s/`REGION_STABILIZATION`'s observed scores (~100-144, flat
  100.0) are themselves correct/intentional for these two specific calibration worlds
  (`simq_routing_test`/`hero_guild_routing`), or whether one of THEM is the actual anomaly (e.g. an
  unbounded/mis-scaled competing scorer crowding out every other candidate).
- Propose and implement a real fix — likely a rescaling of `AdventureGoalScorer`'s utility formula
  to be commensurate with the other tier-5 scorers' actual output ranges — NOT a "force route
  selection to win" hack (per this project's own explicit guidance against forcing an unrealistic
  route to fix a low pillar score; a legitimate rescale that lets `ADVENTURE_ROUTE` compete on its
  actual, intended merits is in scope, an artificial thumb-on-the-scale boost is not).
- Once a real fix lands, recalibrate `grade_anchors.json` AGENCY for the 6 run_keys
  `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` left correctly unchanged (they
  currently and correctly read `C/0.0`, matching pre/post-fix measured reality).
- Update `docs/simulation_quality/eval_matrix_results.md`'s AGENCY Cross-World Design Note and the
  2 dated NOTE blocks the originating ticket added (currently factual-not-restoration-claiming) to
  reflect whatever the real, evidence-based outcome turns out to be.

## Out of Scope
- The `last_routing_family`/`last_routing_tick` write-path fix itself — already correctly landed by
  `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`, do not re-touch.
- `evaluate_project_switch()`'s own lock/margin/retention decision logic (STRAT-185/186/187) — not
  touched under any circumstance, same constraint as the originating ticket.
- `last_defer_reason`'s `Bounded` status — unrelated, stays as-is.
- `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift — tracked separately by
  `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`.
- Any change to `COMBAT_ENGAGE`'s or `REGION_STABILIZATION`'s own scoring formulas, UNLESS
  Investigate's own evidence concludes one of THEM (not `AdventureGoalScorer`) is the real anomaly
  — in which case re-scope explicitly, don't assume the fix is on the adventure side by default.

## Acceptance Criteria
- [ ] Root cause of the utility-scale mismatch determined with real evidence (calibration formula
      history, git blame, comparison against other `GoalScorer` output ranges) — not assumed to be
      "adventure's formula is wrong" without checking whether a competing scorer is the actual
      anomaly
- [ ] A real, non-forced fix implemented (rescale, not a win-boost hack) — or, if Investigate
      concludes no fix is warranted (e.g. finds `ADVENTURE_ROUTE` losing is actually
      archetype-correct for these specific worlds, similar to the existing
      `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` precedent for AGENCY=C being correct in
      non-routing worlds), that determination is made explicitly with cited evidence, not silently
      defaulted either way
- [ ] `route_selected`/`action_executed`/`route_family_first_use` verified via a fresh
      `calibrate_simq.py` run to fire (or, if the DA-ruling above concludes 0 is correct, that
      finding is what's verified and documented instead)
- [ ] `grade_anchors.json` AGENCY recalibrated for the 6 run_keys if the fix restores real emission
- [ ] `docs/simulation_quality/eval_matrix_results.md` updated to reflect the real, verified outcome

## Related Tickets
- TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE (BLOCKED — the ticket that fixed the
  real write-path bug and discovered this deeper, separate blocker during its own required AC3
  verification; its own `plan.md` Deviations section and Implementation Notes are the primary
  evidence source for this ticket's scope)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (the architecture change — unconditional standalone
  phase to competing tier-5 `GoalScorer` — that plausibly introduced this scale mismatch)
- TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT (the earlier ticket in this same
  investigation chain that first recalibrated AGENCY down to C/0.0 for these 6 run_keys, correctly,
  given the state at that time)
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA (precedent DA ruling for AGENCY=C being archetype-correct in
  non-routing-capable worlds — relevant precedent, not necessarily applicable here since these ARE
  routing-capable worlds by design)

## Related Docs
- docs/simulation_quality/eval_matrix_results.md (AGENCY Cross-World Design Note)
- docs/guidelines/intentional_divergences.md §2.41
- docs/parity_ledger/infrastructure.yaml (INFRA-237)

## Related Stored Artifacts
- stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/ (once moved — the
  primary evidence source: DEBUG-trace observations of ADVENTURE_ROUTE vs COMBAT_ENGAGE/
  REGION_STABILIZATION utility scores across full 500-tick runs)

## Related Code Areas
- src/ai/goals/adventure_scorer.py (`AdventureGoalScorer.score()`, `_ADVENTURE_ROUTE_SCORE_MAX`)
- src/systems/strategic_systems/intelligence.py (tier-5 goal competition, `evaluate_strategic_intent()`)
- Whatever scorer(s) produce `COMBAT_ENGAGE`'s/`REGION_STABILIZATION`'s competing scores (Investigate
  must locate these — not yet identified precisely in this ticket's own filing)

## Assumptions / Open Questions
- Whether the fix belongs on `AdventureGoalScorer`'s side or a competing scorer's side is
  explicitly NOT pre-decided — Investigate's own evidence must determine this, not an assumption
  that "adventure is the broken one just because it's the one currently under investigation."
- Whether losing tier-5 competition is itself the archetype-correct outcome for these 2 worlds
  (mirroring the `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` precedent) is a real open question this
  ticket's own Investigate/DA phase must resolve, not assume answered by the mere existence of this
  ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
