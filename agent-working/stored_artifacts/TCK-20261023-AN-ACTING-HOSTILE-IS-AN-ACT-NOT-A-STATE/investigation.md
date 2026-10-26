---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE
tags: []
---

# investigation - TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (step B)

Step B is not measured yet. The predictions below come from code and the saved probes (`/mnt/data/scratch-rpg-implementer/paired_en2/wp_raider38.json`, `wp_worker2.json`, `ptt43.json`; reader map `stepB_acting_reader_map.md`). Those probes record hostile position, distance and perceived, but NOT the hostile's task, and not per-tick hits. So "acting" cannot be read from them. What they show:

## Evidence that bears on the prediction
- raider 38 (crowded s46): leader 30 is 2-13 tiles away on 20 samples; hp falls 29 -> 15 between t3640 and t3650 (a hit, with leader 30 at distance 2 at t3640) and 18 -> 0 by t3770 (leader 30 at distance 3 at t3760), so leader 30 does act on raider 38 at times.
- worker 2 (frontier s44): leader 30 at 2 tiles on 8 samples; hp falls 1 per ~10-50 ticks (starvation, 1 hp per 24 ticks, not hits). The ticket already says the leader "sits 2-11 tiles away for about 200 ticks without engaging" (C4's shape).
- guard 11 (crowded s43): terms held on every sample t1984-2140 were WOUNDED, ADJACENT, CLOSING, OUTMATCHED; TARGETED only at t1984-1986. Raider 35 rests and raider 37 sleeps (a resting raider's task is not an attack, a sleeping one's is SLEEP).

## Prediction under step B alone (conditional on the hostile's task, which is the unknown)
- **guard 11:** after t1986 neither raider has an attack/pursuit task against it (resting, sleeping) and no hit lands, so `acting_threat_to` is False. With the guard's hunger escalated (100), the panic hold yields, the guard falls through to the hunger project and eats. Predicted: the ~180-tick hold ends, N-class starvation of guard 11 clears. Unless a resting raider's stale ATTACK task (see plan.md 1, risk) still reads as acting, in which case it holds until that raider decides.
- **raider 38:** leader 30 attacks at times. On ticks within 10 of a hit, or while its task is ATTACK/PURSUE at 38, it is acting and the flight stays; on the other ticks the hold and the row-83 bypass yield and the raider pursues food. Predicted: fewer starved ticks than today but not zero; whether it reaches a meal depends on the leader's activity (about 2 hit windows in the 198 sampled ticks). N15 raider row: improves or stays; unknown without the leader's task trace.
- **worker 2:** leader 30 is resting, not acting (C4's shape). Under B the panic hold yields under escalated hunger. But the winning goal today is `town_return` (about 163.5) over hunger 160 through TownScorer's low-hp term (N13), and B does not touch it, so the worker may still walk to town_center instead of eating. Predicted: the panic flight stops, N15 worker row does not necessarily clear without N13.
- **merchant 37 (row 83, must stay green):** hunter adjacent, not attacking, hunger 100. The bypass was already unconditional at >= 95; B only widens "not a threat" at hunger < 95, and the panic hold yields. The real-kernel test should stay green; check its control arm.

## What to measure first (host-bound, one heavy process)
A probe that logs, per tick for each of the three subjects and each perceived hostile: the hostile's `task.work_kind`, `payload.action`, `navigation.movement_mode`, `target_id`, and `last_hit_tick`/`last_attacker_id` on the subject. That turns the predictions above into counts. It needs the field from plan.md section 2, so it follows the build.
