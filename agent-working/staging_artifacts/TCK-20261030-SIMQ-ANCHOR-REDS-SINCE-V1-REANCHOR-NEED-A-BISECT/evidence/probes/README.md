# Probes P1-P4, P3 faction trace, prefix check and repeat (2026-10-31, rpg-planner ruling 4, 5 and 6)

Measurement only; nothing here edits an anchor. Parent a25619971 against d914bace7 (#769). Every run: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, audit_mode, `tools/evaluate_simq.py --scenario <key>` in-process (same code path as the sweep, anchors file held at one copy), clean `git archive` trees, MemAvailable >= 3 GB, sequential. `probe2.py` logs, for ALL entities: every goal-scorer call (`sc`), every `retreat_pull` call that changes a score (`rp`), and per tick every entity's position, hp, alive, current project, nav target and group (`st`). `probe3.py` (P3 only) logs faction tension and the hostile bond updates behind it. The raw per-tick logs (15 000 state rows per 500t run) stay in scratch (`/data/vboxuser/Work/simq_probes/out/`); this directory holds the scripts, the analysis output and the reports.

Pass rule (ruling 4): (a) every record before the first difference is identical (all entities, scores and state), and (b) the first difference is a score changed by `retreat_pull` and nothing else.

## Result per row

| probe | row(s) | first difference | verdict |
|---|---|---|---|
| P1 | urban_political s123 500t ECONOMY (and s123 1000t by prefix) | t75, entity 5: COMBAT_RETREAT 59.355 to 65.595 | PASS |
| P2 | generated_frontier_3_42 s456 200t COMBAT | t41, entity 19: COMBAT_RETREAT 88.266 to 127.146 | PASS |
| P3 | urban_political s42 500t (all pillars), 200t WORLD/others, 1000t, 2000t by prefix | t42, entity 18: COMBAT_RETREAT 84.519 to 123.399 (at or before t200: yes) | PASS (first difference); the status flips and the 2000t rows go to the designer, see below |
| P4 | selfmodel_execution_probe s42 200t WORLD | t42, entity 18: same values as P3 | PASS |

P1 note (not traced): in P1 the score differences occur at 3 points before the first state difference at t111, and none flips the highest score, yet entity 10's project becomes proj_combat_retreat_110 instead of proj_resolve_blocker_110. So the project choice is not plain maximum score; the arbiter's decision there was not traced.

The first state difference follows the first score difference by one tick in P2, P3, P4 (t42/t43 and t41/t42); in P1 it is t111 (entity 10). No STOP.

### P1: urban_political s123 500t (ECONOMY row)
- first sc difference (tick, entity): (75, 5) | first state difference: (111, 10)
- scorer at that point: ('GoalKind.COMBAT_RETREAT', 59.354971, 65.594971, 'town_center', 'town_center')
- rp calls at this (tick, entity) in d914: [(59.35497108004968, 0.35, 65.59497108004969)] | in parent: None
- VERDICT (b):  PASS: first difference is a COMBAT_RETREAT score changed by retreat_pull, nothing else

### P2: generated_frontier_3_42 s456 200t (COMBAT row)
- first sc difference (tick, entity): (41, 19) | first state difference: (42, 19)
- scorer at that point: ('GoalKind.COMBAT_RETREAT', 88.265999, 127.145999, 'town_center', 'town_center')
- rp calls at this (tick, entity) in d914: [(88.265998873385, 0.25, 127.14599887338501)] | in parent: None
- VERDICT (b):  PASS: first difference is a COMBAT_RETREAT score changed by retreat_pull, nothing else

### P3: urban_political s42 500t (s42 500t rows, the two status flips, and by prefix the 200t, 1000t, 2000t rows)
- first sc difference (tick, entity): (42, 18) | first state difference: (43, 18)
- scorer at that point: ('GoalKind.COMBAT_RETREAT', 84.518796, 123.398796, 'town_center', 'town_center')
- rp calls at this (tick, entity) in d914: [(84.51879572808227, 0.25, 123.39879572808228)] | in parent: None
- VERDICT (b):  PASS: first difference is a COMBAT_RETREAT score changed by retreat_pull, nothing else

### P4: urban_political_selfmodel_execution_probe s42 200t (WORLD row)
- first sc difference (tick, entity): (42, 18) | first state difference: (43, 18)
- scorer at that point: ('GoalKind.COMBAT_RETREAT', 84.518796, 123.398796, 'town_center', 'town_center')
- rp calls at this (tick, entity) in d914: [(84.51879572808227, 0.25, 123.39879572808228)] | in parent: None
- VERDICT (b):  PASS: first difference is a COMBAT_RETREAT score changed by retreat_pull, nothing else

## Per-pillar event counts and the first event difference behind each moved pillar
One table per probe (`P*_pillars.md`; scored events from `quality_scores.jsonl` with event_id excluded; the event_count columns are the pillar's own counts). Small-sample sensitivity the designer should see: P1 ECONOMY moves +0.107 (0.497 to 0.604) on 26 versus 25 scored events; P1 COMBAT 27 versus 26. Counts, P1 / P2 / P3 / P4 files: `P1_pillars.md`, `P2_pillars.md`, `P3_pillars.md`, `P4_pillars.md`.

## P3 status flips
The faction trace (`probe3.py`, the two P3f runs) was run outside the slot go; its results serve ruling 4 if rpg-planner accepts them.

`P3_status_flips.txt`: FACTION no-data (3 events to 0): pair tension between bandit_company and town_council never passes 0.4 at d914bace7 (0.31 at most; 31 hostile bond updates against 51), so there is no NEUTRAL-to-TENSE transition and no stagnant event; the two bond-update streams first differ at t171 (entity 18 acts in the parent, which kills it at t172). COGNITION from no-data (2 to 22 events): 20 `decision_divergence_detected` events for entity 6, t275-294, which fires with a harvesting project and a danger concern 0.8; entity 6 differs from t180 (group 10009), and no `retreat_pull` call touches it. The intermediate links are not individually traced (stated in the file). Whether FACTION's no-data fails evaluate_simq's grade check: it does (REGRESS at s42 500t, 1000t and 2000t at d914bace7, see the sweep README); the anchor is not moved to make that pass; it goes to the designer.

## Prefix check, from the sweep's own run directories (no re-run)
`prefix_check.py`, output `prefix_check_output.md`: for each commit, the full `simulation_events.jsonl` records up to tick N (event_id and run_id excluded; the run-end `*_tally` events at a run's own last tick excluded) and the metric windows up to N are identical between the shorter and the longer run, in order: s42 200t against 500t up to t200, s42 500t against 1000t and 2000t up to t500, s123 500t against 1000t up to t500, at both commits (8 of 8 identical). The runs are looked up by the run_id in each key's own `quality_report.json` because several keys share a world, seed and length. `p3_vs_200t_and_repeat.txt`: the P3 (500t) probe run's events up to t200 equal the sweep's `urban_political_seed42_200t` run at both commits. There is no per-tick state hash in the logs (only the final `state_hash` in `run_manifest.json`, which differs with run length by construction), so the comparison is the full event stream, which is stricter than a hash for the observable behaviour.

## Repeat (P1 at d914bace7, run twice)
Compared byte for byte: the probe logs (`P1_d.jsonl` against `P1_d2.jsonl`, sha256 equal) and the final state hash (`0bd536588c14d9c5` both). `quality_scores.jsonl` compared with event_id excluded: identical, 8011 rows; event_id differs on all 8011 rows because it defaults to uuid4 (`src/observability/events.py:56`). Nothing in the simulation core reads event_id (outside observability and simulation_quality the only readers are campaign post-analysis, which the single-episode path does not run, and source_event_id fields built from category, region and tick strings or from helpers with no callers). The reports' `worst_events` lists differ only in event_id. Result: the sweep's measurements are repeatable; no nondeterminism.

## s42 at d914bace7: the missing second wave (for the designer packet)
`../sweep/freeze_check_output.txt` and `../sweep/freeze_check.py`. The run does not die out: last window alive_entities_avg 21 (parent 16 at 2000t; 19 and 21 at 1000t), events about 2257 per 100 ticks to the last tick. The events per 250 ticks at 2000t are parent 2737 / 5022 / 3740 / 3164 / 2828 / 3427 / 6455 / 5896 and d914bace7 3534 / 4245 / 2889 / 2823 / 2825 / 3914 / 4507 / 5653. Last tick per event type, urban_political s42 2000t:

| event type | parent | d914bace7 |
|---|---|---|
| entity_killed, combat_resolved, combat_damage, combat_engagement_ended, xp_granted | 1809 | 452 |
| combat_engagement_started, combat_initiated | 1780 | 411 |
| near_death_survival | 1806 | 444 |
| resource_harvested, resource_node_depleted | 473 | 298 |
| gold_transaction | 1818 | 1540 |
| quest_event | 153 | 259 |
| world_emergence_event | 1909 | 552 |
| capability_growth_stalled | 726 | 543 |
| social_memory_created | 1720 | still produced after t1990 (the opposite direction) |

Deaths (entity_killed): parent 7, d914bace7 4. The silent stretch and the parent's wave starts (COMBAT t1666, NARRATIVE t1669, PROGRESSION t1709) are from ruling 6. Not traced: what the t1500+ events at d914bace7 are and why no wave forms there.
