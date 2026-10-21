---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT
tags: []
---

# plan - TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT

## Plan
1. `src/engine/tactical.py` `_perceived_threats`: skip neighbours that are not alive (the panic gate sees only the living).
2. `src/engine/cognition.py` `AppraisalSystem.evaluate_emotional_state`: drop dead neighbours at the top (hostile ratio, allies, nemesis, grudge read only the living).
3. `src/engine/cognition.py` `SensoryFilter.filter_saliency`: no +200 hostility bonus for a dead hostile, so corpses stop taking saliency slots from live threats.
4. One real-kernel test file (3 tests), the memo row 84 (1) / SURV-07 text, Bible 04 section 1, parity STRAT-285, divergence 2.136 (docs land in the step-2 docs commit of the same PR).
5. Measure: gate V3 on crowded 45, then the standard paired run 7b1528861 to 23fbe0ecf, seeds 42-46, 5000 ticks.

## Scope guards
No change to grief, mourning or vengeance (they read the death record, `trust_history` and blockers, not appraisal). No hunger re-choice (parked: TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1).

## Acceptance map
Corpse gives no PANIC_RETREAT (test 1); live hostile still does (test 2); hungry hp-2 raider with three townsfolk dead eats (test 3); V3 crowded 45 is 0; paired no drift.
