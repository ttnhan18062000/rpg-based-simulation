---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE
tags: []
---

# test_plan - TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (step B)

## New tests
1. `last_hit_tick`: written by CombatPatch on `damage_taken > 0` with an attacker (also an opportunity hit); not written by a hazard/starvation drain or a zero-damage update; survives `replace`; in `to_canonical_dict`; the canonical hash differs with and without it; equal when equal.
2. `acting_threat_to` pairs per reader, built on the real frontier_living_world s42 merchant/hunter scene (as in `test_starvation_is_a_present_threat_weighed_in_goal_selection.py`):
   - hostile ADJACENT, WOUNDED/OUTMATCHED subject, hostile task resting: not acting; hostile task `ENTITY_ACT` `ATTACK` with `target_id == S`: acting; `ENTITY_MOVE` PURSUE/INTERCEPT `target_id == S`: acting; a bare `target_id == S` with `HOLD`: not acting; `target_id` another entity: not acting.
   - CLOSING alone (stale `last_position`) is not acting.
   - hit window: `last_attacker_id == H` and `tick - last_hit_tick <= NEED_WAKE_CADENCE` acting; one tick past it, not; a different last attacker, not.
3. SURV-07 bypass (`scorers.py:61`, `:69`): at hunger 80, with a resting adjacent hostile the escalation is KEPT; with a targeting hostile it is DROPPED. At hunger >= 95 unchanged.
4. Panic hold (`tactical.py:203-219`):
   - escalated need and a resting hostile: no PANIC_RETREAT, the tick falls through (a held cornered subject eats);
   - escalated need and an acting hostile: PANIC_RETREAT and the freeze as before;
   - no pressing need and a resting hostile: PANIC_RETREAT unchanged.
5. Unchanged-behaviour guards: rest in place, eat carried, eat at carcass, safety retreat still hold back under a resting adjacent hostile.

## Existing pins: triage (S1). "change" needs the planner's named yes; each is confirmed by reading the test at build time
| Test | Verdict | Old -> new |
|---|---|---|
| unit/ai/test_starvation_is_a_present_threat_weighed_in_goal_selection.py::test_a_subject_whose_hunger_is_not_past_its_line_still_has_the_pull_dropped_under_a_threat | CHANGE | hunger 80 with an adjacent hunter that is not attacking: raw 80 (dropped) -> escalated kept. Keep the "dropped" assertion in a scene where the hunter targets the subject. |
| ...::test_a_starving_subject_under_a_present_threat_keeps_its_escalated_hunger_pull | KEEP | unchanged at hunger 100 |
| ...::test_a_wounded_subject_below_its_line_still_flees_the_predator_beside_it | CHECK | hunger 80 inside the hometown with an adjacent hunter: with an escalated-need hold, panic yields at hunger >= 57 only if the hunter is not acting; hunger 80 is pressing, so the verdict depends on the hunter's task. Likely CHANGE (scene needs a targeting hunter to keep PANIC_RETREAT). |
| ...::test_a_subject_in_the_desperation_band_with_a_hunter_really_attacking_does_not_stand_and_eat | CHECK | the hunter's task is set? If it is not attacking, CHANGE (add a targeting task); otherwise KEEP |
| ...::test_the_starving_pull_exceeds_the_retreat_ceiling | KEEP (step A changes it) | |
| integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py | MUST STAY GREEN | the control arm (old gate restored) may need its old-gate restoration updated to the new predicate |
| unit/tactical/test_held_panic_falls_through.py::test_a_held_panic_beside_a_real_tactical_hostile_keeps_the_freeze... | CHECK | hostile acting? hunger pressing? |
| unit/engine/test_pressing_need_wakes_a_held_move.py::test_a_woken_flight_stays_a_flight_while_the_threat_is_present... | CHECK | hunger pressing and the hostile's task |
| unit/combat/test_panic_flight_needs_a_present_threat.py::test_a_cornered_subject_with_a_threat_still_holds_its_tile | KEEP if hunger is not pressing (the common case); CHECK |
| unit/engine/test_safety_retreat_needs_present_threat.py, test_rest_in_place.py, test_eat_carried_before_travel.py | KEEP | A4-A7 unchanged |
| unit/ai/test_opening_steps.py, unit/combat/*, test_p1_semantic_hardening, move-lifecycle tests, test_biological_needs, test_event_shapers, conflict04 | KEEP | no acting-hostile dependency |
| integration/.../test_a_dead_body_is_not_a_perceived_threat_through_the_real_kernel.py | CHECK | "a live hostile in view still panics": hunger pressing? hostile acting? |

## Runs
`tests/unit/ai tests/unit/engine tests/unit/tactical tests/unit/combat tests/unit/strategic` and the two integration tests above, then `-m "not slow"` over the touched domains, with `PYTHONHASHSEED=0 PYTHONPATH=.`, `-n 0 --resource-budget off -p no:cacheprovider`. Lint, mypy gate and `codebase.health check` with `/mnt/data/scratch-deps-venv/bin`.
