---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
phase: inprogress
date: 2026-10-20
tags: []
---

# TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Title
Put both survival pressures on one escalation scale: combat_retreat gets the need-pull escalation once hp is in its own consequence band

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
**Raised to P1, first rpg item after v1 (designer, 2026-10-21).** This shape is behind two of the three v1 owned known reds (v1_disclosure N15), recorded under the user's v1 cutoff of 2026-10-21. In both, a starving subject at near-death hp keeps fleeing a present catalog-hostile (Tier 1, correct by design) until it starves, because hunger and flight are not on one escalation scale.
- crowded_frontier s46, raider 38 (orc_clan), STARVATION at t3778, step 2 f9b21b55b:
  - hp 3-7%, 0 gold, no food;
  - PANIC_RETREAT from leader 30 (goblin_warband, hp 131, 2-13 tiles away) on 131 of 198 ticks between t3580 and t3777, while the hunger project is current;
  - an unthreatened open way existed in 9 of 9 retreat samples (the inn in 6 of 9).
- frontier_living_world s44, worker 2 (town_council), STARVATION at t3736:
  - hp 0.1-1.4%; PANIC_RETREAT from leader 30, predator_hunter 34 and alpha 49 (all catalog-hostile) on 150 of 236 ticks;
  - town_return (about 163.5) beats hunger (160) only through TownScorer's low-hp term (about 59): a wound-driven return to safety, also Tier 1;
  - an unthreatened open way existed in 13 of 19 retreat samples.
- Probes: /mnt/data/scratch-rpg-implementer/probes_hs/ways_probe.py and tick_log.py; data in /mnt/data/scratch-rpg-implementer/paired_en2/wp_raider38.json, wp_worker2.json and paired_en/v3btr/.
- The parked safe-route step (TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1) moves only the objective, so it cannot clear a tactical panic. The design here has to put the two pulls on one scale.
- Related: worker 2's goblin leader sits 2-11 tiles away for about 200 ticks without engaging, which is C4's shape (a hunter beside a subject without engaging, decision 47).

This is backlog, parked by the designer on 2026-10-20. Build it only if data shows a subject eating into a fatal attack.

V3 step (ii), on rpg-v3-starvation-threat at 70402779d, keeps the escalated hunger pull under a present threat once hunger is past STARVING_LINE (95). At the goal level, that pull is 155-160: raw hunger plus ESCALATION_AMPLITUDE 60 (need_pull.py). CombatRetreatScorer is 100·(1−hp_ratio) + 50·panic − 30·bravery, with a ceiling of 150, so the starving pull beats every reachable retreat score. The designer ruled the weighing is by immediacy: an acting threat still pre-empts in the tactical pass. The long-run unification it noted is to escalate retreat the same way, so both pressures saturate on one scale and the appraised threat decides.

## Scope
- Apply the existing ESCALATION_AMPLITUDE and smoothstep to combat_retreat once hp is past its consequence line. No new constant.
- Measure it as its own step: paired 3 × 42-46, crowded first. Retreat changes in every world.

## Out of Scope
- Any change to the hunger pull or to tactical ordering.

## Acceptance Criteria
- At hunger 95+, a strong enough appraised threat makes retreat outscore hunger, pinned by a unit test.
- The paired measurement passes the stop line, or the result goes to the owner.

## Related Tickets
- the V3 step (ii) ticket on rpg-v3-starvation-threat (SURV-07, memo row 83)

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1
- docs/world_rules SURV-07

## Related Stored Artifacts
- none

## Related Code Areas
- src/ai need_pull.py (ESCALATION_AMPLITUDE, smoothstep)
- scorers.py CombatRetreatScorer (~213-240)

## Assumptions / Open Questions
- Design point to rule here (designer, 2026-10-21): "a hostile acting on the subject" (owner_decision_memo rows 83 and 84, N3) is read today by `present_threat_to` (src/ai/goals/present_threat.py:23-26), whose terms in src/engine/tactical_threat.py:60-78 are states: WOUNDED (hp < 0.7), ADJACENT (≤ 1.0), CLOSING, OUTMATCHED (≥ 1.5×) or TARGETED. Any one term counts. So a hostile resting beside a wounded subject counts as acting.
  - Evidence: crowded s43 guard 11 on step 2 (f9b21b55b). present_threat_to is True on every sample from t1984 to t2140 with only WOUNDED, ADJACENT and OUTMATCHED held, while raider 35 rests and raider 37 sleeps. The guard holds in place for about 180 ticks, starving (hunger 100, -1 hp per 24 ticks), and its hunger project is never served (probe probes_hs/ptt_probe.py).
  - The designer will rule here that "acting" becomes an act (targeted, attacking or moving at the subject), not a state. The tactical hold (tactical.py:209) and the goal-level weighing (SURV-07 (ii)) must share that one definition.
  - Disclosed in v1 in C4's row.
- The trigger is evidence of a fatal eat-under-attack. Without it, this stays parked.

## Implementation Notes
After v1, only if the trigger is seen.
- 2026-10-23, rpg-planner brief: this ticket is STEP A only, the retreat escalation in CombatRetreatScorer, measured as its own paired step (`--base 341f700d0`, seeds 42-46, 3 worlds, 5000 ticks, crowded first, after the planner says the host is free). It does not touch `present_threat_to`, `tactical_threat.py` or `tactical.py:209`. STEP B, "acting" meaning an act and not a state, is its own ticket on this branch, filed after the designer rules, and is measured with step A's tip as its parent.
- 2026-10-27, paired run 8d76615ba vs 3533fde71 STOPPED (frontier_living_world: blacksmiths 2 to 0, merchants 15 to 21 dead, worker HAZARD 5 to 10). Offline attribution (`/mnt/data/scratch-rpg-implementer/stepA/attr/SUMMARY.md`): divergence always starts at the first COMBAT_RETREAT flight, and the deaths cascade through hostile leader id30 (seeds 42, 43). Context for the ruling (`attr/flight_context.txt`, a proxy: hp trend plus nearest kinds, faction guessed; present_threat_to is not in the files): of 75 flights in the 5-seed, 3-world probe, 65 were issued with no acting hostile, and 58 of those came while the subject was regenerating with same-side kinds adjacent. Only 7 had lost hp in the 30 ticks before. Flights re-issued every 20-100 ticks per entity.
- 2026-10-27, rpg-designer ruling option (i) via rpg-planner, reversing "no acting gate": the COMBAT_RETREAT flight is issued only on a brain decision tick where `acting_threat_to` holds, and a held one ends at the first brain decision tick where it does not (read on decision ticks only). No present-threat gate; CombatRetreatScorer unchanged. Built in `combat_retreat_flight.py` (the act is passed as a thunk from `intelligence.py`, so it is read only when a COMBAT_RETREAT project or flight is in play). Docs: 2.139 "Flight" bullet, parity STRAT-289. The Bible 02 §7 CONFLICT-04 sentence is with the designer for wording. A new paired run on the gated build replaces the stopped one.
- Review note (health, 2026-10-27): the gate first raised one NEW row (ruff PLR0913, 6 params on `combat_retreat_flight_update`) and made intelligence.py one line longer (an import). Both were fixed structurally, with no baseline edit: the module derives the current project id itself (the same expression as `intelligence.py`, `strat_up` is not reassigned in between; covered by a new test), and `acting_threat_to` is re-exported from `src.ai.goals` onto the existing import line. Health: 0 new, the same 3 recorded "worse" rows on intelligence.py as at 8d76615ba (override already recorded).
- The hp consequence line and the threat gate are proposed in `agent-working/staging_artifacts/TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE/plan.md`. No code is written until the designer confirms them.

## Test Summary

## Files Changed

## Completion Summary
