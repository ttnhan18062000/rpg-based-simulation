---
status: historical
layer: testing
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261028-RE-RECORD-BASELINE-V1-UNDER-FLAT-SHA256-V3
date: 2026-10-28
tags: [benchmarking]
---

# Evidence: v1 base re-recorded under flat-sha256-v3

Run on 2026-10-28 from 01:08 to 06:55 (+07:00) on u24desktop:
`tools.rpg_measure.paired --base 957caf8f6 --new 04b85fb2e --report-only --seeds 42 .. 51 --self-check full --jobs 2`,
with PYTHONHASHSEED=0 and cache `/mnt/data/scratch-rpg-implementer-2/v3/cache`. The run returned rc=0 and verdict
`{"mode": "report_only", "outcome": "PASS"}`. Base-vs-base self-check (full, 30 runs): spread 0.

R arm (v3) results: `results/957caf8f6cff-72320cac-5000/` (30 files). It is copied to
`/mnt/data/scratch-rpg-measure/results/957caf8f6cff-72320cac-5000/` (diff-checked) and the original copy is kept.
sha256 of the sorted per-file sha256 list: `48e379775b923edcb6f6efa66e142f957ab25c3ae86ae4d788ce4ea332480444`.

## 1. F1 moves only digests: R (v3, 957caf8f6) vs P (v2, 04b85fb2e)

Every field in a paired result is compared. start_hash and final_hash must differ, and every other field must be equal.

| world | seed | non-digest fields equal | start_hash differs | final_hash differs |
|---|---|---|---|---|
| frontier_living_world | 42 | yes | yes | yes |
| frontier_living_world | 43 | yes | yes | yes |
| frontier_living_world | 44 | yes | yes | yes |
| frontier_living_world | 45 | yes | yes | yes |
| frontier_living_world | 46 | yes | yes | yes |
| frontier_living_world | 47 | yes | yes | yes |
| frontier_living_world | 48 | yes | yes | yes |
| frontier_living_world | 49 | yes | yes | yes |
| frontier_living_world | 50 | yes | yes | yes |
| frontier_living_world | 51 | yes | yes | yes |
| urban_political | 42 | yes | yes | yes |
| urban_political | 43 | yes | yes | yes |
| urban_political | 44 | yes | yes | yes |
| urban_political | 45 | yes | yes | yes |
| urban_political | 46 | yes | yes | yes |
| urban_political | 47 | yes | yes | yes |
| urban_political | 48 | yes | yes | yes |
| urban_political | 49 | yes | yes | yes |
| urban_political | 50 | yes | yes | yes |
| urban_political | 51 | yes | yes | yes |
| crowded_frontier | 42 | yes | yes | yes |
| crowded_frontier | 43 | yes | yes | yes |
| crowded_frontier | 44 | yes | yes | yes |
| crowded_frontier | 45 | yes | yes | yes |
| crowded_frontier | 46 | yes | yes | yes |
| crowded_frontier | 47 | yes | yes | yes |
| crowded_frontier | 48 | yes | yes | yes |
| crowded_frontier | 49 | yes | yes | yes |
| crowded_frontier | 50 | yes | yes | yes |
| crowded_frontier | 51 | yes | yes | yes |

non-digest mismatches: 0 of 30

## 2. Attribution of the v1 differences (report-only)

Byte comparison (`cmp`) of the cached arms, seeds 42-46, 3 worlds (15 files each):

| step | arms compared | identical |
|---|---|---|
| v1 record = v1 record commit | e6a6a3e10 vs 341f700d0 | 15/15 |
| step B (2.138, measured) | 341f700d0 vs 265162719 | moved (2.138 Measured line) |
| step B tip = #753 merge | 265162719 vs 3533fde71 | 15/15 |
| #753 merge = P | 3533fde71 vs 04b85fb2e | 15/15 |
| P -> R | 04b85fb2e vs 957caf8f6 | digests only (section 1) |

So on seeds 42-46 every difference between v1 and R is step B. Seeds 47-51 have no cached intermediate arm, because the
2.138 measurement covered s42-46. There, the v1 differences are attributed by the diff classing (investigation.md)
only and are not byte-proven. rpg-planner ruled that no extra run is needed, since this concerns the report-only v1
attribution, not the F1 proof.

## 3. R vs v1 (e6a6a3e10), per world (report-only)

### frontier_living_world

| seed | start equal | adds equal | counters equal | fates differing (id: v1 -> new) |
|---|---|---|---|---|
| 42 | yes | yes | no | 0 |
| 43 | yes | yes | no | 5: 3: [0, 'HAZARD', 'worker'] -> [1, None, 'worker']; 5: [1, None, 'worker'] -> [0, 'DEFEAT', 'worker']; 13: [0, 'HAZARD', 'blacksmith'] -> [1, None, 'blacksmith']; 30: [0, 'COMBAT', 'leader'] -> [1, None, 'leader']; 52: [0, 'COMBAT', 'wild_creature'] -> [1, None, 'wild_creature'] |
| 44 | yes | yes | no | 7: 2: [0, 'STARVATION', 'worker'] -> [0, 'COMBAT', 'worker']; 7: [0, 'HAZARD', 'worker'] -> [0, 'COMBAT', 'worker']; 11: [0, 'HAZARD', 'guard'] -> [0, 'DEFEAT', 'guard']; 17: [0, 'COMBAT', 'scout'] -> [1, None, 'scout']; 36: [1, None, 'merchant'] -> [0, 'COMBAT', 'merchant']; 50: [0, 'COMBAT', 'wild_creature'] -> [0, 'DEFEAT', 'wild_creature']; ... (+1) |
| 45 | yes | yes | no | 5: 4: [1, None, 'worker'] -> [0, 'HAZARD', 'worker']; 30: [0, 'HAZARD', 'leader'] -> [1, None, 'leader']; 51: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature']; 53: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature']; 54: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature'] |
| 46 | yes | yes | no | 3: 5: [0, 'HAZARD', 'worker'] -> [1, None, 'worker']; 15: [0, 'DEFEAT', 'scout'] -> [1, None, 'scout']; 51: [0, 'COMBAT', 'wild_creature'] -> [1, None, 'wild_creature'] |
| 47 | yes | yes | no | 0 |
| 48 | yes | yes | no | 2: 4: [1, None, 'worker'] -> [0, 'DEFEAT', 'worker']; 24: [1, None, 'raider'] -> [0, 'DEFEAT', 'raider'] |
| 49 | yes | yes | no | 4: 27: [0, 'DEFEAT', 'raider'] -> [1, None, 'raider']; 28: [1, None, 'scout'] -> [0, 'COMBAT', 'scout']; 51: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature']; 52: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature'] |
| 50 | yes | yes | no | 0 |
| 51 | yes | yes | no | 5: 6: [0, 'HAZARD', 'worker'] -> [0, 'COMBAT', 'worker']; 11: [0, 'HAZARD', 'guard'] -> [1, None, 'guard']; 24: [0, 'COMBAT', 'raider'] -> [0, 'DEFEAT', 'raider']; 50: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature']; 51: [1, None, 'wild_creature'] -> [0, 'COMBAT', 'wild_creature'] |

### urban_political

| seed | start equal | adds equal | counters equal | fates differing (id: v1 -> new) |
|---|---|---|---|---|
| 42 | yes | yes | no | 4: 1: [0, 'COMBAT', 'worker'] -> [0, 'DEFEAT', 'worker']; 2: [0, 'DEFEAT', 'worker'] -> [1, None, 'worker']; 13: [0, 'COMBAT', 'blacksmith'] -> [1, None, 'blacksmith']; 22: [0, 'COMBAT', 'hero'] -> [1, None, 'hero'] |
| 43 | yes | yes | yes | 0 |
| 44 | yes | yes | no | 6: 1: [0, 'DEFEAT', 'worker'] -> [1, None, 'worker']; 9: [0, 'DEFEAT', 'guard'] -> [1, None, 'guard']; 13: [0, 'COMBAT', 'blacksmith'] -> [1, None, 'blacksmith']; 16: [0, 'DEFEAT', 'scout'] -> [0, 'COMBAT', 'scout']; 17: [0, 'DEFEAT', 'scout'] -> [0, 'COMBAT', 'scout']; 28: [0, 'STARVATION', 'merchant'] -> [1, None, 'merchant'] |
| 45 | yes | yes | yes | 0 |
| 46 | yes | yes | no | 0 |
| 47 | yes | yes | no | 0 |
| 48 | yes | yes | yes | 0 |
| 49 | yes | yes | yes | 0 |
| 50 | yes | yes | no | 1: 14: [0, 'DEFEAT', 'scout'] -> [0, 'COMBAT', 'scout'] |
| 51 | yes | yes | yes | 0 |

### crowded_frontier

| seed | start equal | adds equal | counters equal | fates differing (id: v1 -> new) |
|---|---|---|---|---|
| 42 | yes | yes | no | 5: 12: [1, None, 'merchant'] -> [0, 'COMBAT', 'merchant']; 23: [0, 'COMBAT', 'scout'] -> [0, 'DEFEAT', 'scout']; 30: [1, None, 'leader'] -> [0, 'STARVATION', 'leader']; 34: [0, 'DEFEAT', 'raider'] -> [0, 'COMBAT', 'raider']; 38: [0, 'COMBAT', 'raider'] -> [1, None, 'raider'] |
| 43 | yes | yes | no | 2: 1: [0, 'HAZARD', 'worker'] -> [0, 'COMBAT', 'worker']; 35: [1, None, 'raider'] -> [0, 'COMBAT', 'raider'] |
| 44 | yes | yes | no | 0 |
| 45 | yes | yes | no | 8: 2: [0, 'COMBAT', 'worker'] -> [0, 'DEFEAT', 'worker']; 5: [0, 'COMBAT', 'worker'] -> [0, 'HAZARD', 'worker']; 11: [0, 'DEFEAT', 'guard'] -> [0, 'COMBAT', 'guard']; 13: [0, 'COMBAT', 'blacksmith'] -> [0, 'DEFEAT', 'blacksmith']; 22: [0, 'DEFEAT', 'scout'] -> [0, 'COMBAT', 'scout']; 29: [0, 'COMBAT', 'scout'] -> [0, 'DEFEAT', 'scout']; ... (+2) |
| 46 | yes | yes | no | 8: 1: [0, 'HAZARD', 'worker'] -> [0, 'COMBAT', 'worker']; 10: [0, 'DEFEAT', 'guard'] -> [0, 'COMBAT', 'guard']; 12: [1, None, 'merchant'] -> [0, 'COMBAT', 'merchant']; 23: [0, 'DEFEAT', 'scout'] -> [0, 'COMBAT', 'scout']; 24: [0, 'COMBAT', 'raider'] -> [0, 'DEFEAT', 'raider']; 27: [0, 'DEFEAT', 'raider'] -> [1, None, 'raider']; ... (+2) |
| 47 | yes | yes | no | 11: 4: [0, 'COMBAT', 'worker'] -> [0, 'DEFEAT', 'worker']; 8: [0, 'COMBAT', 'worker'] -> [0, 'STARVATION', 'worker']; 16: [0, 'COMBAT', 'scout'] -> [0, 'DEFEAT', 'scout']; 18: [0, 'DEFEAT', 'merchant'] -> [0, 'COMBAT', 'merchant']; 22: [0, 'COMBAT', 'scout'] -> [0, 'DEFEAT', 'scout']; 25: [0, 'COMBAT', 'raider'] -> [0, 'DEFEAT', 'raider']; ... (+5) |
| 48 | yes | yes | no | 6: 4: [0, 'DEFEAT', 'worker'] -> [0, 'COMBAT', 'worker']; 6: [1, None, 'worker'] -> [0, 'DEFEAT', 'worker']; 7: [0, 'DEFEAT', 'worker'] -> [0, 'HAZARD', 'worker']; 14: [1, None, 'scout'] -> [0, 'COMBAT', 'scout']; 30: [0, 'DEFEAT', 'leader'] -> [0, 'COMBAT', 'leader']; 31: [1, None, 'hero'] -> [0, 'DEFEAT', 'hero'] |
| 49 | yes | yes | no | 15: 1: [0, 'COMBAT', 'worker'] -> [0, 'HAZARD', 'worker']; 4: [0, 'DEFEAT', 'worker'] -> [0, 'COMBAT', 'worker']; 6: [0, 'COMBAT', 'worker'] -> [0, 'HAZARD', 'worker']; 7: [0, 'DEFEAT', 'worker'] -> [0, 'COMBAT', 'worker']; 10: [0, 'COMBAT', 'guard'] -> [0, 'HAZARD', 'guard']; 17: [0, 'COMBAT', 'scout'] -> [0, 'DEFEAT', 'scout']; ... (+9) |
| 50 | yes | yes | no | 3: 6: [0, 'COMBAT', 'worker'] -> [0, 'DEFEAT', 'worker']; 31: [0, 'COMBAT', 'hero'] -> [0, 'DEFEAT', 'hero']; 32: [0, 'COMBAT', 'hero'] -> [0, 'DEFEAT', 'hero'] |
| 51 | yes | yes | no | 7: 7: [0, 'COMBAT', 'worker'] -> [0, 'HAZARD', 'worker']; 10: [0, 'DEFEAT', 'guard'] -> [0, 'HAZARD', 'guard']; 11: [0, 'COMBAT', 'guard'] -> [0, 'DEFEAT', 'guard']; 14: [0, 'DEFEAT', 'scout'] -> [0, 'COMBAT', 'scout']; 32: [0, 'COMBAT', 'hero'] -> [0, 'HAZARD', 'hero']; 33: [0, 'DEFEAT', 'hero'] -> [0, 'COMBAT', 'hero']; ... (+1) |

## 4. Paired report (R as base, P as new)

## Paired measurement: step (div -) - REPORT-ONLY

- base 957caf8f6cff -> new 04b85fb2eee8; frontier_living_world, urban_political, crowded_frontier; seeds [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]; 5000 ticks; PYTHONHASHSEED=0; audit_mode and signals_zeroed recorded True in every run of both arms
- base-vs-base self-check (full, 30 runs): spread 0 (byte-identical final and start hashes, fates and counters)
- SE = sd(per-seed new-base)/sqrt(10); STOP = more people deaths by > 2·SE AND > floor (1 per seed = 10 total); fewer past both is REPORT-ONLY; SD 0 is not special-cased

### frontier_living_world

People deaths (tick-0 base roster, keeps_coin, by id; n=33 per seed): base [22, 19, 31, 22, 29, 30, 25, 30, 28, 20] -> new [22, 19, 31, 22, 29, 30, 25, 30, 28, 20]
- total 256 -> 256 (delta +0); mean per-seed delta +0.00, SE 0.00, floor 10 total; verdict (more deaths past 2·SE and the floor stops, fewer is report-only): **no drift**

| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |
|---|---|---|---|---|---|
| alpha | 1 | 1 | +0.00 | 0.00 |  |
| blacksmith | 6 | 6 | +0.00 | 0.00 |  |
| guard | 38 | 38 | +0.00 | 0.00 |  |
| leader | 6 | 6 | +0.00 | 0.00 |  |
| merchant | 35 | 35 | +0.00 | 0.00 |  |
| predator_hunter | 5 | 5 | +0.00 | 0.00 |  |
| raider | 39 | 39 | +0.00 | 0.00 |  |
| scout | 77 | 77 | +0.00 | 0.00 |  |
| sentinel | 10 | 10 | +0.00 | 0.00 |  |
| wild_creature | 53 | 53 | +0.00 | 0.00 |  |
| worker | 55 | 55 | +0.00 | 0.00 |  |

Deaths by kind|cause (death_record), rows that moved: none
Alive at end by kind (sum of seeds): alpha 9->9, blacksmith 4->4, guard 12->12, leader 4->4, merchant 25->25, predator_hunter 85->85, raider 1->1, scout 3->3, sentinel 50->50, wild_creature 7->7, worker 25->25
Added after tick 0 (count of seeds' ids): base 0 -> new 0
REPORT-ONLY reading: STOP is suppressed; extinct in the new arm only: none
Extinctions: STOP none; base-state (extinct in both arms) none; recovered none

- flee ticks: 199419 -> 199419
- flee episodes: 8662 -> 8662
- pursuit ticks: 62699 -> 62699
- pursuit episodes: 2138 -> 2138
- entity-samples that perceived a hostile: 48142 -> 48142
- steps (all terrain): 587447 -> 587447
- perception samples taken per run: [500] (perceived_hostiles every 10 ticks)
- steps onto cave: 101656 -> 101656
- steps onto forest: 26328 -> 26328
- steps onto plain: 309152 -> 309152
- steps onto road: 47286 -> 47286
- steps onto ruin: 101028 -> 101028
- steps onto swamp: 1997 -> 1997
- pre-check refusals: not measured (no typed record exists at this commit)

### urban_political

People deaths (tick-0 base roster, keeps_coin, by id; n=30 per seed): base [14, 9, 11, 16, 10, 14, 12, 9, 9, 12] -> new [14, 9, 11, 16, 10, 14, 12, 9, 9, 12]
- total 116 -> 116 (delta +0); mean per-seed delta +0.00, SE 0.00, floor 10 total; verdict (more deaths past 2·SE and the floor stops, fewer is report-only): **no drift**

| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |
|---|---|---|---|---|---|
| blacksmith | 3 | 3 | +0.00 | 0.00 |  |
| guard | 22 | 22 | +0.00 | 0.00 |  |
| hero | 2 | 2 | +0.00 | 0.00 |  |
| merchant | 38 | 38 | +0.00 | 0.00 |  |
| scout | 34 | 34 | +0.00 | 0.00 |  |
| worker | 17 | 17 | +0.00 | 0.00 |  |

Deaths by kind|cause (death_record), rows that moved: none
Alive at end by kind (sum of seeds): blacksmith 7->7, guard 28->28, hero 28->28, merchant 52->52, scout 6->6, worker 63->63
Added after tick 0 (count of seeds' ids): base 0 -> new 0
REPORT-ONLY reading: STOP is suppressed; extinct in the new arm only: none
Extinctions: STOP none; base-state (extinct in both arms) none; recovered none

- flee ticks: 8207 -> 8207
- flee episodes: 181 -> 181
- pursuit ticks: 28569 -> 28569
- pursuit episodes: 605 -> 605
- entity-samples that perceived a hostile: 4907 -> 4907
- steps (all terrain): 382718 -> 382718
- perception samples taken per run: [500] (perceived_hostiles every 10 ticks)
- steps onto plain: 378210 -> 378210
- steps onto road: 4508 -> 4508
- pre-check refusals: not measured (no typed record exists at this commit)

### crowded_frontier

People deaths (tick-0 base roster, keeps_coin, by id; n=38 per seed): base [37, 37, 35, 34, 36, 34, 28, 35, 32, 34] -> new [37, 37, 35, 34, 36, 34, 28, 35, 32, 34]
- total 342 -> 342 (delta +0); mean per-seed delta +0.00, SE 0.00, floor 10 total; verdict (more deaths past 2·SE and the floor stops, fewer is report-only): **no drift**

| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |
|---|---|---|---|---|---|
| blacksmith | 9 | 9 | +0.00 | 0.00 |  |
| guard | 47 | 47 | +0.00 | 0.00 |  |
| hero | 28 | 28 | +0.00 | 0.00 |  |
| leader | 9 | 9 | +0.00 | 0.00 |  |
| merchant | 29 | 29 | +0.00 | 0.00 |  |
| raider | 65 | 65 | +0.00 | 0.00 |  |
| scout | 79 | 79 | +0.00 | 0.00 |  |
| worker | 76 | 76 | +0.00 | 0.00 |  |

Deaths by kind|cause (death_record), rows that moved: none
Alive at end by kind (sum of seeds): blacksmith 1->1, guard 3->3, hero 2->2, leader 1->1, merchant 1->1, raider 25->25, scout 1->1, worker 4->4
Added after tick 0 (count of seeds' ids): base 0 -> new 0
REPORT-ONLY reading: STOP is suppressed; extinct in the new arm only: none
Extinctions: STOP none; base-state (extinct in both arms) none; recovered none

- flee ticks: 31364 -> 31364
- flee episodes: 1990 -> 1990
- pursuit ticks: 44839 -> 44839
- pursuit episodes: 2632 -> 2632
- entity-samples that perceived a hostile: 12993 -> 12993
- steps (all terrain): 208435 -> 208435
- perception samples taken per run: [500] (perceived_hostiles every 10 ticks)
- steps onto forest: 17309 -> 17309
- steps onto plain: 172950 -> 172950
- steps onto road: 18176 -> 18176
- pre-check refusals: not measured (no typed record exists at this commit)

### Watch-table rows (cumulative table, D76) - REPORT-ONLY reading, never trips a stop

| Step | Div | World | People deaths base->new | Delta | SE | Extinctions |
|---|---|---|---|---|---|---|
| step | - | frontier_living_world | 256->256 | +0 | 0.00 | none |
| step | - | urban_political | 116->116 | +0 | 0.00 | none |
| step | - | crowded_frontier | 342->342 | +0 | 0.00 | none |
