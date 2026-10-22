---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT

## Title
A dead body in the neighbour view is not a perceived threat: the panic gate, the emotional appraisal and the saliency ranking skip the dead

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Raider 27 of crowded_frontier seed 45 (the v1 gate's V3 death, t1091) shuttled on y=40 between the corpses of workers 2, 3 and guard 11 and the inn until it starved. The neighbour view lists dead entities; the tactical panic gate (`_perceived_threats`) had no alive test, so a hp-2 raider fled from corpses every ~10 ticks while the brain tick (which filters the dead) saw nothing to avoid. Designer ruling (via rpg-planner): option B alone, before v1; one defect, so appraisal and saliency stay in the same step.

## Scope
- `TacticalDecisionSystem._perceived_threats` skips non-alive entities.
- `AppraisalSystem.evaluate_emotional_state` ignores dead neighbours (hostile ratio, allies, nemesis, grudge).
- `SensoryFilter.filter_saliency` gives a dead body no hostility bonus.
- Audit of every neighbour-view and hostile reader (list under Implementation Notes).

## Out of Scope
- The hunger re-choice (parked: TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1).
- Blacksmith 13's hunger-100/no-project state on crowded s45 (its own trace).

## Acceptance Criteria
- A corpse in view gives no PANIC_RETREAT; a live hostile in view still does; a hungry hp-2 raider with the three townsfolk dead on its walk reaches a meal and eats.
- V3 crowded 45 is 0 (gate harness).

## Related Tickets
- TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED (parked), TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1

## Related Docs
- docs/mechanics/04_strategic_cognition.md (section 1), docs/guidelines/intentional_divergences.md (2.136), docs/parity_ledger/strategic_cognition.yaml (STRAT-285), docs/plans/systemic_world/owner_decision_memo.md (row 84 (1)), docs/plans/systemic_world/v1_disclosure.md (N7)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT/ (plan, investigation, test_plan).

## Related Code Areas
- src/engine/tactical.py, src/engine/cognition.py

## Assumptions / Open Questions
- Grief, mourning and vengeance do not read appraisal's ally/nemesis lists: grief reads the death record and `trust_history` (src/core/grief_triggers.py), the heir's nemesis comes from strategic blockers (lifecycle.py), campaign nemesis from campaign state.

## Implementation Notes
Audit (get_neighbor_view and every are_entities_hostile reader). Already filtered on alive: intelligence.py 152 and 444, intake.py 35, scorers.py 180, scorers_support perceived_hostiles, cooperation/providers 53, combat.py 496, legality get_engaged_hostiles_at_pos, classify_neighbours (via perceives). Fixed here: tactical._perceived_threats, appraisal (and its callers domain/cognition 57, CombatRetreatScorer, intelligence 1020), saliency. Not hostile reads: intelligence 592/914 salience (dead-ally grief branch wants corpses), worker_logic/actions/kernel neighbour views feeding action execution, spatial_query, combat_engagement phase (filters alive). Occupancy maps are alive-only.

## Test Summary
tests/integration/observability/test_a_dead_body_is_not_a_perceived_threat_through_the_real_kernel.py (3): (a) and (c) fail without the fix, (b) passes both ways.

## Files Changed
src/engine/tactical.py, src/engine/cognition.py, the test file above.

## Completion Summary
Done on branch rpg-corpse-not-a-threat (23fbe0ecf, step one of the v1 fix PR; the docs land in the step-two docs commit of the same PR).

- **Divergence**: 2.136 (class Bug Fix); parity STRAT-285; memo row 84 (1); v1 disclosure N7.
- **Measured**: paired 7b1528861 to 23fbe0ecf, seeds 42-46, 5000 ticks, base-vs-base self-check byte-identical (the report was regenerated from the cache after the original log was deleted; same numbers). People deaths: frontier 142 to 130 (SE 2.23), urban 58 to 62 (SE 0.37), crowded 166 to 167 (SE 0.66); no drift. Extinction stop in crowded (guard, merchant), accepted by the owner, 2026-10-21. Traces: seed 42 raider 35 stopped fleeing nine corpses at t396 and killed guard 10 at t471; seed 44 merchant 12 killed at t2066 in a melee that exists only in the new arm (v1 row C6); seed 46 raider 34, no longer distracted by worker 1's corpse at t1407, killed merchant 12 at t1436.
- **Gate**: V3 on crowded 45 is 0 (the case that motivated the change).
- **Tests**: the three real-kernel tests above pass; full tests/unit serial on the PR tip: 8442 passed, 9 failures are the pre-existing SimQ grade anchors (red on 7b1528861 too, TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED).
- **Mechanism advisory** (report-only): `mechanism_registry_changed_code_check` names `tactical_decision` (cites `src/engine/tactical.py`) and `emotion` (cites `src/engine/cognition.py`) as mechanisms whose cited code changed without their own entry changing. The change narrows who counts as a threat (only the living); it adds no mechanism and removes none, so I judged no entry edit needed, and `registries/mechanisms.yaml` content is the planner's to rule on; reported to rpg-planner.
- **Known limits**: grief, mourning and vengeance are unchanged by design; C6 (a subject in a fight it chose never disengages) and C7 (mutual threatening-flee standoff) surfaced after this change and are independent of it, filed as after-v1 tickets.
