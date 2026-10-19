---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS
date: 2026-10-15
tags: []
---

# Base-vs-base proof (63b98e76b both arms): the full 15-run repeat of the base arm was byte-identical (spread 0) on all 3 worlds x seeds 42-46 x 5000 ticks; the table below was rendered from the cached arm with --self-check off, with the final verdict wording.

## Paired measurement: self-check (base-vs-base) (div -)

- base 63b98e76bdf0 -> new 63b98e76bdf0; frontier_living_world, urban_political, crowded_frontier; seeds [42, 43, 44, 45, 46]; 5000 ticks; PYTHONHASHSEED=0; audit_mode and signals_zeroed recorded True in every run of both arms
- base-vs-base self-check (off, 0 runs): spread 0 (byte-identical final and start hashes, fates and counters)
- SE = sd(per-seed new-base)/sqrt(5); STOP = more people deaths by > 2·SE AND > floor (1 per seed = 5 total); fewer past both is REPORT-ONLY; SD 0 is not special-cased

### frontier_living_world

People deaths (tick-0 base roster, keeps_coin, by id; n=33 per seed): base [30, 20, 29, 31, 29] -> new [30, 20, 29, 31, 29]
- total 139 -> 139 (delta +0); mean per-seed delta +0.00, SE 0.00, floor 5 total; verdict (more deaths past 2·SE and the floor stops, fewer is report-only): **no drift**

| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |
|---|---|---|---|---|---|
| blacksmith | 4 | 4 | +0.00 | 0.00 |  |
| guard | 22 | 22 | +0.00 | 0.00 |  |
| leader | 3 | 3 | +0.00 | 0.00 |  |
| merchant | 23 | 23 | +0.00 | 0.00 |  |
| raider | 19 | 19 | +0.00 | 0.00 |  |
| scout | 35 | 35 | +0.00 | 0.00 |  |
| sentinel | 7 | 7 | +0.00 | 0.00 |  |
| wild_creature | 22 | 22 | +0.00 | 0.00 |  |
| worker | 33 | 33 | +0.00 | 0.00 |  |

Deaths by kind|cause (death_record), rows that moved: none
Alive at end by kind (sum of seeds): alpha 5->5, blacksmith 1->1, guard 3->3, leader 2->2, merchant 7->7, predator_hunter 45->45, raider 1->1, scout 5->5, sentinel 23->23, wild_creature 8->8, worker 7->7
Added after tick 0 (count of seeds' ids): base 0 -> new 0
Extinctions: STOP none; base-state (extinct in both arms) none; recovered none

- flee ticks: 69042 -> 69042
- flee episodes: 3515 -> 3515
- pursuit ticks: 21909 -> 21909
- pursuit episodes: 1116 -> 1116
- entity-samples that perceived a hostile: 19657 -> 19657
- steps (all terrain): 245909 -> 245909
- perception samples taken per run: [500] (perceived_hostiles every 10 ticks)
- steps onto cave: 54022 -> 54022
- steps onto forest: 13858 -> 13858
- steps onto plain: 115142 -> 115142
- steps onto road: 19588 -> 19588
- steps onto ruin: 42471 -> 42471
- steps onto swamp: 828 -> 828
- pre-check refusals: not measured (no typed record exists at this commit)

### urban_political

People deaths (tick-0 base roster, keeps_coin, by id; n=30 per seed): base [13, 9, 12, 9, 11] -> new [13, 9, 12, 9, 11]
- total 54 -> 54 (delta +0); mean per-seed delta +0.00, SE 0.00, floor 5 total; verdict (more deaths past 2·SE and the floor stops, fewer is report-only): **no drift**

| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |
|---|---|---|---|---|---|
| blacksmith | 2 | 2 | +0.00 | 0.00 |  |
| guard | 10 | 10 | +0.00 | 0.00 |  |
| hero | 2 | 2 | +0.00 | 0.00 |  |
| merchant | 18 | 18 | +0.00 | 0.00 |  |
| scout | 17 | 17 | +0.00 | 0.00 |  |
| worker | 5 | 5 | +0.00 | 0.00 |  |

Deaths by kind|cause (death_record), rows that moved: none
Alive at end by kind (sum of seeds): blacksmith 3->3, guard 15->15, hero 13->13, merchant 27->27, scout 3->3, worker 35->35
Added after tick 0 (count of seeds' ids): base 0 -> new 0
Extinctions: STOP none; base-state (extinct in both arms) none; recovered none

- flee ticks: 2162 -> 2162
- flee episodes: 118 -> 118
- pursuit ticks: 9506 -> 9506
- pursuit episodes: 256 -> 256
- entity-samples that perceived a hostile: 2000 -> 2000
- steps (all terrain): 195228 -> 195228
- perception samples taken per run: [500] (perceived_hostiles every 10 ticks)
- steps onto plain: 194205 -> 194205
- steps onto road: 1023 -> 1023
- pre-check refusals: not measured (no typed record exists at this commit)

### crowded_frontier

People deaths (tick-0 base roster, keeps_coin, by id; n=38 per seed): base [34, 31, 36, 32, 34] -> new [34, 31, 36, 32, 34]
- total 167 -> 167 (delta +0); mean per-seed delta +0.00, SE 0.00, floor 5 total; verdict (more deaths past 2·SE and the floor stops, fewer is report-only): **no drift**

| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |
|---|---|---|---|---|---|
| blacksmith | 5 | 5 | +0.00 | 0.00 |  |
| guard | 23 | 23 | +0.00 | 0.00 |  |
| hero | 14 | 14 | +0.00 | 0.00 |  |
| leader | 3 | 3 | +0.00 | 0.00 |  |
| merchant | 12 | 12 | +0.00 | 0.00 |  |
| raider | 35 | 35 | +0.00 | 0.00 |  |
| scout | 38 | 38 | +0.00 | 0.00 |  |
| worker | 37 | 37 | +0.00 | 0.00 |  |

Deaths by kind|cause (death_record), rows that moved: none
Alive at end by kind (sum of seeds): guard 2->2, hero 1->1, leader 2->2, merchant 3->3, raider 10->10, scout 2->2, worker 3->3
Added after tick 0 (count of seeds' ids): base 0 -> new 0
Extinctions: STOP none; base-state (extinct in both arms) ['blacksmith']; recovered none

- flee ticks: 20805 -> 20805
- flee episodes: 1588 -> 1588
- pursuit ticks: 21554 -> 21554
- pursuit episodes: 1407 -> 1407
- entity-samples that perceived a hostile: 7032 -> 7032
- steps (all terrain): 103808 -> 103808
- perception samples taken per run: [500] (perceived_hostiles every 10 ticks)
- steps onto forest: 12649 -> 12649
- steps onto plain: 77054 -> 77054
- steps onto road: 14105 -> 14105
- pre-check refusals: not measured (no typed record exists at this commit)

### Watch-table rows (cumulative table, D76)

| Step | Div | World | People deaths base->new | Delta | SE | Extinctions |
|---|---|---|---|---|---|---|
| self-check (base-vs-base) | - | frontier_living_world | 139->139 | +0 | 0.00 | none |
| self-check (base-vs-base) | - | urban_political | 54->54 | +0 | 0.00 | none |
| self-check (base-vs-base) | - | crowded_frontier | 167->167 | +0 | 0.00 | none |
