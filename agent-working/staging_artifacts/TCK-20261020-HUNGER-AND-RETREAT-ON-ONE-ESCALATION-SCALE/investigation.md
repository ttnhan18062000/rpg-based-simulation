---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
tags: []
---

# investigation - TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A)

## What is there today (main 341f700d0)
- `src/ai/goals/scorers.py:212-242` CombatRetreatScorer computes `100*(1-hp_ratio) + 50*panic_level - 30*bravery`, floored at 0. It returns 0 when `hp_ratio >= 0.5` and the subject is not fleeing. The goal targets `town_center`. Nothing caps it at 150; 150 is only the formula's maximum (hp 0, panic 1, bravery 0). Two consequences:
  - The score is nonzero whenever hp < 0.5, even with no hostile in view.
  - It has no threat gate of its own; the panic term is the only threat input.
- `src/engine/need_pull.py:21-23,51-55`: `need_pull = raw + ESCALATION_AMPLITUDE(60) * smoothstep(ONSET 0.6, FULL 0.85, arrival_fraction)`. At hunger 95-100 the pull is 155-160 (pinned by `test_the_starving_pull_exceeds_the_retreat_ceiling...`).
- `scorers.py:61-75`: below STARVING_LINE (95), a need's escalation is dropped while `present_threat_to` holds. Past 95 it is kept (row 83).
- `present_threat_to` (`src/ai/goals/present_threat.py:23`) requires at least one catalog hostile perceived within `ENTITY_TARGET_PERCEPTION_RADIUS` (10, saliency cap 5) and at least one term from `tactical_threat.py:60-78`. WOUNDED (hp < 0.7) is one of those terms, so a wounded subject meets it whenever it perceives any hostile.
- `src/engine/cognition.py:129-163`: panic is +0.8 when hp < 0.1, +0.5 when hp < 0.2, +0.2 when hp < 0.4. It gets +0.3 when outnumbered more than 2:1, plus dread and grudge, minus 0.3*bravery. The subject is fleeing when panic > 0.4.
- **The N15 flight is not decided at the goal level.** `tactical.py:203-219` runs PANIC_RETREAT whenever `emotion.is_fleeing and threats` (and a destination exists or a tactical hostile is present). That runs before any project or objective is consumed, so no goal score, retreat or hunger, reaches those ticks. Step A changes only which goal wins on the ticks where the tactical pass does not pre-empt.

## Prediction per N15 case, step A alone (gated on present_threat_to; see plan)
Bravery comes from `compile_world`, assumed constant. Samples come from `paired_en2/wp_raider38.json` and `wp_worker2.json`, every 10 ticks.
- **crowded_frontier s46, raider 38** (bravery 0.645, hp 3-7%):
  - Panic is 0.8 - 0.19 = 0.61 (fleeing). Raw retreat is 93-97 + 30.3 - 19.4, about 104-108.
  - Step A adds the full 60 (hp < 15%), giving about 164-168 against hunger at 156-160. Retreat now wins the goal by about 4-12.
  - On the 9 non-panic samples (task None), leader 30 is perceived within 10 tiles on 6. On those, present_threat_to holds (WOUNDED plus a perceived hostile), so the goal flips from hunger to COMBAT_RETREAT (town_center).
  - The panic ticks are unchanged (tactical pass).
  - **Predicted:** no tick gains a hunger pursuit, and the subject loses the hunger goal on most of its remaining free ticks. Starvation stays, possibly earlier. The project may also churn between hunger and retreat at the edge of the 10-tile radius. N15 does not clear and is likely worse, as the planner expected.
- **frontier_living_world s44, worker 2** (bravery 0.344, hp 0.1-1.4%):
  - Panic is 0.8 - 0.10 = 0.70. Raw retreat is about 98.6 + 34.8 - 10.3, about 123. Step A gives about 183, above town_return (about 163.5) and hunger (160).
  - Today town_return already wins and targets town_center, the same target as COMBAT_RETREAT.
  - **Predicted:** the winning goal changes from town_return to combat_retreat while a hostile is within 10 tiles. That is 23 of 25 samples (only 3710-3730 have none within 10).
  - The destination is the same, and no tick gains a hunger pursuit. Starvation stays. N15 does not clear.
  - This case also needs the N13 item (town_return outbids an escalated need) or step B.
- **Conclusion:** step A alone clears neither N15 row. It moves the goal-level winner toward retreat on exactly the ticks where step B's "acting" ruling would say the hostile is not acting (leader 30 resting 2-13 tiles away). The N15 rows need step B, and worker 2 may also need N13. This prediction comes from code reading and the sampled probes. The paired step A measurement is the check.

## Ungated variant (rejected; shown for the designer)
Without the present_threat_to gate, any subject at hp < 0.4 with no hostile in view gets up to +60 retreat. For raider 38 that is about 164 > 160, so a wounded starving subject alone in a field would walk to town_center instead of eating. That breaks SURV-07 ("only a present threat outranks a pressing need") in every world.

## Wider effect (every world)
With the gate, every subject at hp < 0.4 that perceives any catalog hostile within 10 gets the retreat escalation, because WOUNDED alone satisfies present_threat_to. Retreat then beats hunger and sleep at their lines (155-160), town_return (about 135-165), recover (at most 120) and engage (at most 100). This is a behaviour change in every world, expected by the ticket.

## Test pin affected
`tests/unit/ai/test_starvation_is_a_present_threat_weighed_in_goal_selection.py::test_the_starving_pull_exceeds_the_retreat_ceiling_so_the_weighing_is_by_immediacy_not_score_magnitude` asserts retreat <= 150 < 155. Step A falsifies it by design. This is a test-expectation change and needs the planner's (and the designer's) yes. The proposal is to replace it with the ticket's acceptance pin.

## Step A alone undoes row 83's own fix (computed, 2026-10-23)
This uses the row 83 unit scene: frontier_living_world s42, merchant 37, hp 10/85, bravery 0.108, hunger 100, predator_hunter 45 adjacent and not attacking.
- Today: raw retreat 108.4, eat 160.0, and `present_threat_to` True, so the merchant eats. That is the v1 gate's V3 death, fixed by row 83.
- Step A (hp 0.118 is inside the full band): retreat becomes 168.4 > 160.0, so the merchant takes the retreat goal and does not eat.
- `tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py` is expected to go red. The gate's V3 starvation check on frontier s42 is at risk of coming back.
- The cause is that present_threat_to counts a state (WOUNDED plus ADJACENT plus OUTMATCHED) as a present threat, so a watching hunter scales retreat. Row 83 says "the subject eats with a wolf watching". Step A's gate needs step B's "acting" test, not `present_threat_to` as it is today.
- **Options for the planner/designer:**
  - (1) Build step B first, then step A gated on the "acting" test.
  - (2) Fold A and B into one measured step.
  - (3) Measure A alone as evidence only, never landed.
  - (4) Gate A today on a narrower existing term (TARGETED only, `tactical_threat.py:69`), with no change to `present_threat_to`. This is a step B decision taken early, so it is the designer's call.
