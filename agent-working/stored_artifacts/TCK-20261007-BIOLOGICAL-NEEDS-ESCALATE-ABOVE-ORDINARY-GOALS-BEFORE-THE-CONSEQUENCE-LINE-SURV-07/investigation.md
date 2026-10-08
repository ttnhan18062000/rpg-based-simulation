---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07
artifact_type: investigation
tags: [strategy, cognition]
---

# Investigation

## Census (before the change; main + #403/#404/#406; seed 42, `audit_mode`, 1500 ticks)
Highest ordinary goal utilities among goals with a target (p50 / p90 / max): `region_stabilization` 100 flat; `resolve_blocker` 89.4 / 101.9 / 103.8; `combat_engage` 105.8 / 144.3 / 150; `town_return` 39.3 / 67.9 / 134.8; `harvesting` 11 / 25 / 95.2; `recover` 39 / 40 / 119; `combat_retreat` 42 / 80 / 130. The need goals were the raw need (hunger 0 to 100; sleep debt, plus 30 at night). Among entities with hunger of at least 60 or sleep debt of at least 40, the winners were `region_stabilization` (264 / 356 on the two worlds) and `resolve_blocker` (234 / 166); need goals won 0 times. Distance to the inn when sleep debt was at least 20: p50 49 / 42, p90 189 / 72, max 192 / 87 tiles. Consequence lines: hunger 95 (+0.1/tick base), sleep deprivation 98 (+0.05/tick base); a worst walk of about 190 ticks adds 19 hunger points or 9.5 sleep-debt points.

## What the first measurement showed (seed 42, one tree)
With the curve alone, DEFEAT deaths rose (`crowded_frontier` 6 to 27, `urban_political` 4 to 14) and `urban_political` alive at t=1100 went 4 to 0. `probes/death_trace.py` showed 19 of 27 and 6 of 14 DEFEATs had the hunger project for all 21 ticks before death, with a present threat at death: the need goal kept winning, and re-winning after the tactical pass suspended it, while a hostile was adjacent. The scorers do not see hostiles, so the fix is a present-threat gate inside the scorers (`present_threat_to`): a perceived, catalog-hostile neighbour plus AGENCY-07's `present_threat_terms`. A wound alone, with no hostile in view, is not a threat (planner ruling).

## Per-entity trace of the remaining hunger deaths (`probes/hunger_defeats.py`, `urban_political`, seed 42, gated)
5 hunger-project DEFEAT deaths of 13. At the tick the goal started other-faction entities were within 3 tiles of the Manhattan path to the inn in all 5 (2, 3, 2, 6, 10; this counts any other faction, so it overstates hostility). 4 of 5 had 0 gold and the fifth 3, so none could have paid the 5-gold meal. Four died within a few tiles of the inn.

## Tactical-contact check (`probes/contact.py`, `probes/hpsrc.py`; entities 22, 2, 28)
Every hp loss was an opportunity attack (`MovementSystem.resolve_move`, `movement.py:292`, COMB-009/272) by scouts 14 and 15 (-17 hp per hit; -15 for the merchant), taken when the victim stepped while adjacent to a perceived hostile. No attacker's task named the victim, so a "who targets me" trace shows nothing. `safety_pressure` was 0.0 for all three (below the 0.75 cautious bar, so AGENCY-07's retreat cannot fire), and the tactical pass did not run on most of those ticks. Separate defect: `TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP`.

## Free meals (`probes/free_eat.py`, gated arm, seed 42)
Every `CoreActions.execute_survival("EAT")` call was by a subject with under 5 gold: `crowded_frontier` 21 of 21, `urban_political` 11 of 11. The `EAT` action consumes no carried food, needs no building and takes no gold, and the inn's 5-gold charge clamps at zero gold (`InventoryService.apply_update`: `gold = max(0, gold + delta)`). SURV-06 rules out free eating, so part of any starvation gain is free meals. An arm that made `EatScorer` offer the inn only to a subject that can pay (branch `rpg-need-affordability`, not shipped) starved every broke subject: starvation 25.0 to 29.8, 25.8 to 26.8, 16.0 to 21.4 and alive at t=1100 5.6 to 0.2, 8.4 to 5.8, 6.8 to 0.0. That change moves with Decision 27 (the poor subject's redirect) and the free-meal ticket `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL`, in one change.

## Measurement conditions and determinism
Every run in the table: seeds 42 to 46, 1500 ticks, `audit_mode`, `max_tick_budget_ms` 1e9, `LocalSequentialExecutor`, and a governor pinned to NORMAL (the `_PinnedNormalGovernor` pattern, with `force_mode` returning None) passed to `Kernel`. Determinism check: `urban_political`, seed 42, four runs started together under extra CPU load (two busy loops plus other runs), two pinned and two unpinned: identical final-state digest (`7dcdbd0856cde37a`) and identical deaths (30; HAZARD 2, DEFEAT 3, COMBAT 1, STARVATION 24). One world, one seed, four runs; an earlier unpinned 30-run batch was discarded and everything was re-run pinned. Sleep debt builds at 0.05 per tick, so the line (98) is reached at about t=1960 and 0.85 of it at about t=1670, which is why rest in place never fired in 1500 or 3000 ticks.

## Five-seed measurement (arms: base = `origin/main` `0a03c2448`; gated = this ticket; gatedA = the affordability branch, not shipped)
Full table with per-seed values (seed order 42, 43, 44, 45, 46) in `probes/five_seed_table.txt`; probes in `probes/` (`need_ms.py` with `run_ms.sh`).

| world | metric | base mean (SD) | gated mean (SD) | gatedA mean (SD) |
|---|---|---|---|---|
| crowded_frontier | alive t=1000 | 18.2 (4.1) | 7.8 (2.2) | 15.8 (3.6) |
| crowded_frontier | alive t=1100 | 5.6 (4.2) | 3.8 (2.0) | 0.2 (0.4) |
| crowded_frontier | deaths | 34.2 (4.1) | 36.8 (1.3) | 38.6 (0.5) |
| crowded_frontier | starvation | 25.0 (1.4) | 13.2 (1.9) | 29.8 (3.7) |
| crowded_frontier | DEFEAT | 5.6 (3.2) | 18.6 (1.8) | 5.4 (3.0) |
| frontier_living_world | alive t=1000 | 14.6 (3.8) | 15.8 (1.9) | 12.8 (3.4) |
| frontier_living_world | alive t=1100 | 8.4 (1.1) | 13.6 (3.5) | 5.8 (1.5) |
| frontier_living_world | deaths | 44.6 (0.5) | 42.4 (3.4) | 46.6 (1.7) |
| frontier_living_world | starvation | 25.8 (5.0) | 13.0 (4.8) | 26.8 (4.1) |
| frontier_living_world | DEFEAT | 10.0 (4.9) | 18.6 (4.6) | 10.8 (4.3) |
| urban_political | alive t=1000 | 14.4 (2.5) | 12.2 (3.0) | 11.8 (2.8) |
| urban_political | alive t=1100 | 6.8 (2.3) | 6.8 (3.5) | 0.0 (0.0) |
| urban_political | deaths | 23.6 (1.8) | 23.8 (3.0) | 30.0 (0.0) |
| urban_political | starvation | 16.0 (1.2) | 10.8 (2.3) | 21.4 (3.9) |
| urban_political | DEFEAT | 3.4 (0.9) | 7.6 (5.1) | 4.2 (1.3) |

Per-seed values for the gated and base arms of the metrics that bear on the acceptance bar:
- alive t=1000: crowded_frontier base [21, 20, 16, 22, 12], gated [9, 4, 8, 9, 9]; frontier_living_world base [17, 18, 10, 17, 11], gated [13, 17, 18, 15, 16]; urban_political base [15, 11, 14, 18, 14], gated [9, 11, 13, 17, 11].
- alive t=1100: crowded_frontier base [4, 7, 4, 12, 1], gated [4, 2, 4, 7, 2]; frontier_living_world base [9, 10, 7, 8, 8], gated [9, 13, 18, 12, 16]; urban_political base [4, 6, 8, 10, 6], gated [2, 5, 9, 11, 7].
- total deaths: crowded_frontier base [35, 35, 37, 27, 37], gated [36, 38, 38, 35, 37]; frontier_living_world base [44, 45, 45, 45, 44], gated [45, 46, 40, 43, 38]; urban_political base [26, 24, 23, 21, 24], gated [28, 25, 22, 20, 24].
- starvation: crowded_frontier base [26, 26, 26, 23, 24], gated [13, 14, 16, 11, 12]; frontier_living_world base [29, 27, 29, 27, 17], gated [14, 18, 14, 14, 5]; urban_political base [18, 15, 15, 16, 16], gated [11, 12, 13, 11, 7].

Poverty split: every starvation death in the gated and affordability arms was a subject with under 5 gold at death on every seed where it was recorded (`starved_could_pay` 0 on all gatedA runs and on urban_political gated; 1 death on frontier_living_world seed 43).

## Acceptance bar and result
Planner's bar (mean starvation down on every world; mean total deaths not up by more than one SD; mean alive at t=1000 and t=1100 not worse by more than one SD, SD from the base arm): starvation passes on all three worlds; total deaths pass; alive at t=1100 passes; alive at t=1000 passes on two worlds and **fails on `crowded_frontier` (18.2 to 7.8)**, owned by the opportunity-attack ticket. The starvation gain includes free meals (above).
