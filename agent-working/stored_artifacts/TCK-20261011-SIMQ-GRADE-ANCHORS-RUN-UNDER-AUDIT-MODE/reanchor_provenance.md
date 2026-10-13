---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE
phase: done
date: 2026-10-13
tags: [simulation-quality, grade-thresholds, determinism, regression]
---

# Re-anchor provenance: grade anchors under audit_mode

Recorded from runs, never typed (baseline_change_policy.md rules 1-5 and 7). The moved rows are listed in the committed before/after table `reanchor_table.tsv` (computed by `tools/test_architecture/simq_reanchor.py` from the run rows, rule 3).

## Cause of this move
- Cause: PR #536 (main `b396080cc`) changes hunting, grazing, healing, upkeep and services on every world; the committed anchors were last changed 2026-08-31 (#90) and were already stale (61 of 81 keys drifted before this). FACTION=0 on dungeon_crawl, sandbox and about 45 rows has its own cause: b1ab4cc92 / PR #198 (2026-09-15) moved diplomacy from an ambient per-faction `tension_level` cascade (blanket HOSTILE/ALLIED states) to directed pairwise_tension, so 200-2000t runs have no diplomatic transitions. Not a regression.
- Ticket: TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE. PR: #531.
- Why audit_mode: the anchors graded host speed (the governor throttle changes with load); under audit_mode the pressure signals are zero, so a run is deterministic.

## Owner ruling (rule 5)
rpg-planner, 2026-10-12: "main behaviour since 08-31, measured with the governor pinned"; all moved rows accepted, per world and pillar, FACTION=0 included. Relayed by testing-planner (cross-session, 2026-10-12). Excluded rows: none. No FACTION known-reds.
Note: rpg is asking rpg-designer whether diplomacy should fire within about 2000 ticks. If it should, the FACTION anchors move again later, by design, under an rpg ticket.
The ruling was given on the stage-2 measurement taken before #536; after #536 merged the measurement was repeated (below) and testing-planner directed the re-anchor on that main (2026-10-13).

## Proof setup (recorded_at 2026-10-13T09:19:05Z; stale_after: none, grade anchors have no staleness mechanism yet)
- Branch `testing-anchors-audit`, proof SHA `a329112a29ab55b59c597523bfaefad1dca4f75d` (a merge of main `b396080cc8ffc8368052c1d72ff36948de3d7bf0` = #536); `src/` identical to main (`git diff origin/main -- src` empty) and a clean tree: clean-src flag TRUE. Runs 2026-10-13T08:54:01Z to 2026-10-13T09:19:05Z, 4 workers, host 6 cores.
- Each anchored run: `python -m tools.calibrate_simq --name <world> --profile <profile> --seed <seed> --ticks <ticks> --output <dir> --audit-mode` (the argv `evaluate_simq` builds), in a fresh process with a unique run id (`<world>_<seed>_<ticks>_<pid>_<uuid8>`); run dirs removed by id. Driver: stage2b.py (scratchpad, not committed; its rows are `rows.jsonl`).
- Why unique ids: the Kernel default run id is `run_<unix second>_<seeded suffix>`, identical for every same-seed process, so two same-second runs share a run directory and double events (rpg ticket TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES). A frozen-clock regression test pins `_run_engine`.

## Identity: 81 of 81 anchors, 2 isolated audit_mode runs each, identical on every pillar (grade, normalized score, raw score, event count) and overall
| run_key | wall_s | run ids (run 1 / run 2) | identical |
|---|---|---|---|
| crowded_frontier_seed123_200t | 13.1 / 13.2 | crowded_frontier_123_200_233600_1ca106ea / crowded_frontier_123_200_233615_4035eaa9 | yes |
| crowded_frontier_seed42_200t | 15.4 / 15.7 | crowded_frontier_42_200_233181_ecb3aec2 / crowded_frontier_42_200_233187_0471e0e2 | yes |
| crowded_frontier_seed456_200t | 13.4 / 13.5 | crowded_frontier_456_200_233781_e72f0e0c / crowded_frontier_456_200_233782_1200a727 | yes |
| dungeon_crawl_seed123_1000t | 29.5 / 28.1 | dungeon_crawl_123_1000_224793_632538a3 / dungeon_crawl_123_1000_224804_426a1200 | yes |
| dungeon_crawl_seed123_2000t | 67.7 / 64.3 | dungeon_crawl_123_2000_226900_49d06137 / dungeon_crawl_123_2000_227052_218c4104 | yes |
| dungeon_crawl_seed123_500t | 15.3 / 15.5 | dungeon_crawl_123_500_224202_20c8a571 / dungeon_crawl_123_500_224229_b3d935df | yes |
| dungeon_crawl_seed42_1000t | 30.3 / 30.8 | dungeon_crawl_42_1000_223385_f0e4ccbb / dungeon_crawl_42_1000_223434_f35fa5e0 | yes |
| dungeon_crawl_seed42_2000t | 62.9 / 67.4 | dungeon_crawl_42_2000_226366_5a38ea09 / dungeon_crawl_42_2000_226568_b9fe4a13 | yes |
| dungeon_crawl_seed42_200t | 10.9 / 11.1 | dungeon_crawl_42_200_222841_8c160e51 / dungeon_crawl_42_200_222846_db934178 | yes |
| dungeon_crawl_seed42_500t | 16.1 / 13.3 | dungeon_crawl_42_500_224169_0ac18e43 / dungeon_crawl_42_500_224173_9392411b | yes |
| dungeon_crawl_seed456_1000t | 24.1 / 25.7 | dungeon_crawl_456_1000_225382_31b1e530 / dungeon_crawl_456_1000_225427_d1c5fc5b | yes |
| dungeon_crawl_seed456_2000t | 56.6 / 58.4 | dungeon_crawl_456_2000_227127_e80ea160 / dungeon_crawl_456_2000_227139_7524472e | yes |
| dungeon_crawl_seed456_500t | 15.1 / 13.5 | dungeon_crawl_456_500_224237_4e8d4620 / dungeon_crawl_456_500_224245_0b8d04bc | yes |
| frontier_extended_seed123_200t | 31.0 / 29.8 | frontier_extended_123_200_228415_28295b08 / frontier_extended_123_200_228644_95aaf48c | yes |
| frontier_extended_seed42_200t | 38.9 / 41.6 | frontier_extended_42_200_227948_a262a143 / frontier_extended_42_200_227970_f85d0a6d | yes |
| frontier_extended_seed456_200t | 33.4 / 35.9 | frontier_extended_456_200_229078_0fb4b29a / frontier_extended_456_200_229215_f0e37dcd | yes |
| frontier_living_world_seed123_200t | 32.5 / 29.8 | frontier_living_world_123_200_230464_b88e7e68 / frontier_living_world_123_200_230698_9e180d32 | yes |
| frontier_living_world_seed42_200t | 35.3 / 35.1 | frontier_living_world_42_200_229645_4b17fa8c / frontier_living_world_42_200_230030_76393f52 | yes |
| frontier_living_world_seed456_200t | 28.5 / 27.7 | frontier_living_world_456_200_230792_5d415cd2 / frontier_living_world_456_200_230853_d345b924 | yes |
| frontier_marches_seed123_200t | 26.8 / 26.9 | frontier_marches_123_200_234471_729b1492 / frontier_marches_123_200_234474_93beabc3 | yes |
| frontier_marches_seed42_200t | 26.7 / 26.6 | frontier_marches_42_200_234332_9bb4d3c8 / frontier_marches_42_200_234355_3b5630fc | yes |
| frontier_marches_seed456_200t | 29.4 / 29.7 | frontier_marches_456_200_235292_acabc6a3 / frontier_marches_456_200_235299_c100d4fb | yes |
| generated_frontier_3_42_seed123_200t | 13.8 / 13.9 | generated_frontier_3_42_123_200_239935_7e7221b0 / generated_frontier_3_42_123_200_239941_10732b7a | yes |
| generated_frontier_3_42_seed42_1000t | 92.1 / 91.8 | generated_frontier_3_42_42_1000_240050_1dd00ea8 / generated_frontier_3_42_42_1000_240051_7e16b22b | yes |
| generated_frontier_3_42_seed42_200t | 14.1 / 14.1 | generated_frontier_3_42_42_200_239814_28ee8934 / generated_frontier_3_42_42_200_239817_f29c8fb7 | yes |
| generated_frontier_3_42_seed456_200t | 13.2 / 13.1 | generated_frontier_3_42_456_200_239988_dcbd4ace / generated_frontier_3_42_456_200_239990_8626a964 | yes |
| hero_guild_routing_seed123_500t | 25.9 / 25.7 | hero_guild_routing_123_500_232732_9ab4bcf2 / hero_guild_routing_123_500_232740_9f0755a2 | yes |
| hero_guild_routing_seed42_1000t | 102.2 / 101.8 | hero_guild_routing_42_1000_236624_7394c511 / hero_guild_routing_42_1000_236652_85bf5074 | yes |
| hero_guild_routing_seed42_500t | 40.9 / 40.8 | hero_guild_routing_42_500_232443_4efeb95d / hero_guild_routing_42_500_232446_ecae24dd | yes |
| hero_guild_routing_seed456_500t | 32.2 / 32.0 | hero_guild_routing_456_500_233087_ae82f405 / hero_guild_routing_456_500_233089_110cfc23 | yes |
| highland_traverse_seed123_200t | 6.9 / 6.8 | highland_traverse_123_200_231405_b901ce93 / highland_traverse_123_200_231409_ee119419 | yes |
| highland_traverse_seed42_200t | 6.2 / 6.1 | highland_traverse_42_200_231263_e34db389 / highland_traverse_42_200_231329_499b4285 | yes |
| highland_traverse_seed456_200t | 6.7 / 6.5 | highland_traverse_456_200_231432_32399904 / highland_traverse_456_200_231461_2da36fed | yes |
| lifecycle_full_coverage_world_seed42_200t | 13.4 / 13.4 | lifecycle_full_coverage_world_42_200_240473_82438704 / lifecycle_full_coverage_world_42_200_240479_f993382c | yes |
| quest_dense_frontier_seed123_200t | 4.1 / 4.0 | quest_dense_frontier_123_200_240334_2acff84b / quest_dense_frontier_123_200_240335_81586630 | yes |
| quest_dense_frontier_seed42_200t | 3.9 / 3.9 | quest_dense_frontier_42_200_240314_9e9825a6 / quest_dense_frontier_42_200_240315_797e5d30 | yes |
| quest_dense_frontier_seed456_200t | 4.0 / 4.1 | quest_dense_frontier_456_200_240360_872d4e86 / quest_dense_frontier_456_200_240361_f733a69a | yes |
| resource_dense_basin_seed123_200t | 9.2 / 9.3 | resource_dense_basin_123_200_233958_569ccf5f / resource_dense_basin_123_200_233960_1d612fb0 | yes |
| resource_dense_basin_seed42_200t | 8.3 / 7.9 | resource_dense_basin_42_200_233783_761807fd / resource_dense_basin_42_200_233786_a009f246 | yes |
| resource_dense_basin_seed456_200t | 7.5 / 7.5 | resource_dense_basin_456_200_234151_1921ecc2 / resource_dense_basin_456_200_234155_cab08473 | yes |
| sandbox_world_seed137_200t | 14.4 / 16.4 | sandbox_world_137_200_222601_45014db0 / sandbox_world_137_200_222602_ce1f8311 | yes |
| sandbox_world_seed42_1000t | 96.9 / 90.9 | sandbox_world_42_1000_223563_b68e30c5 / sandbox_world_42_1000_223605_e3688566 | yes |
| sandbox_world_seed42_2000t | 238.6 / 234.9 | sandbox_world_42_2000_227891_8a8c9268 / sandbox_world_42_2000_227947_020fe492 | yes |
| sandbox_world_seed42_200t | 17.9 / 15.2 | sandbox_world_42_200_222596_583c0fd0 / sandbox_world_42_200_222598_18a3f828 | yes |
| sandbox_world_seed999_200t | 16.4 / 16.2 | sandbox_world_999_200_222791_f156f176 / sandbox_world_999_200_222799_b4f417cf | yes |
| simq_routing_test_seed123_500t | 39.3 / 43.3 | simq_routing_test_123_500_223615_9c2df4f5 / simq_routing_test_123_500_223650_986f2e27 | yes |
| simq_routing_test_seed42_1000t | 94.8 / 94.7 | simq_routing_test_42_1000_237492_4de73e73 / simq_routing_test_42_1000_237517_966b0365 | yes |
| simq_routing_test_seed42_500t | 56.3 / 60.4 | simq_routing_test_42_500_223013_458f630b / simq_routing_test_42_500_223018_52c7d2c1 | yes |
| simq_routing_test_seed456_500t | 57.3 / 55.8 | simq_routing_test_456_500_223948_ee8ef599 / simq_routing_test_456_500_224014_249691c4 | yes |
| simq_scale_stress_seed42_seed42_200t | 23.1 / 23.3 | simq_scale_stress_seed42_42_200_240386_84f95539 / simq_scale_stress_seed42_42_200_240390_3fb0dae2 | yes |
| swamp_border_world_seed123_200t | 10.3 / 10.4 | swamp_border_world_123_200_231538_ce8b269f / swamp_border_world_123_200_231552_e0f74a40 | yes |
| swamp_border_world_seed42_200t | 11.7 / 11.8 | swamp_border_world_42_200_231510_767a2895 / swamp_border_world_42_200_231524_5ba83827 | yes |
| swamp_border_world_seed456_200t | 11.9 / 12.1 | swamp_border_world_456_200_231650_4dcc4a5f / swamp_border_world_456_200_231656_7da58967 | yes |
| unit_faction_tension_seed123_200t | 9.1 / 9.5 | unit_faction_tension_123_200_231758_9539929e / unit_faction_tension_123_200_231830_137f2c37 | yes |
| unit_faction_tension_seed42_1000t | 58.6 / 58.6 | unit_faction_tension_42_1000_238109_9eb69af3 / unit_faction_tension_42_1000_238114_cfdec046 | yes |
| unit_faction_tension_seed42_2000t | 148.6 / 147.6 | unit_faction_tension_42_2000_238768_a2679487 / unit_faction_tension_42_2000_238773_e637a121 | yes |
| unit_faction_tension_seed42_200t | 7.6 / 7.9 | unit_faction_tension_42_200_231666_ff9bdc2f / unit_faction_tension_42_200_231699_3ff8903b | yes |
| unit_faction_tension_seed456_200t | 8.7 / 8.8 | unit_faction_tension_456_200_231831_daa58ae4 / unit_faction_tension_456_200_231834_30be1a56 | yes |
| unit_information_density_seed123_200t | 5.7 / 5.7 | unit_information_density_123_200_240141_3f1b2b92 / unit_information_density_123_200_240142_784991a3 | yes |
| unit_information_density_seed42_200t | 6.0 / 5.9 | unit_information_density_42_200_240059_840b2b12 / unit_information_density_42_200_240062_3284901a | yes |
| unit_information_density_seed456_200t | 5.8 / 5.8 | unit_information_density_456_200_240164_4c2aa9f7 / unit_information_density_456_200_240165_5128cf6f | yes |
| unit_information_source_seed123_200t | 5.7 / 5.7 | unit_information_source_123_200_232021_a1d4b812 / unit_information_source_123_200_232022_44b1de96 | yes |
| unit_information_source_seed42_200t | 6.5 / 5.9 | unit_information_source_42_200_231952_7b0b6cb4 / unit_information_source_42_200_231990_c43f7fda | yes |
| unit_information_source_seed456_200t | 6.2 / 6.4 | unit_information_source_456_200_232118_ba65b08d / unit_information_source_456_200_232134_1806dd16 | yes |
| unit_selfmodel_pilot_seed123_200t | 8.5 / 8.3 | unit_selfmodel_pilot_123_200_232214_2e9a27b8 / unit_selfmodel_pilot_123_200_232262_0ca8297a | yes |
| unit_selfmodel_pilot_seed42_1000t | 77.5 / 78.6 | unit_selfmodel_pilot_42_1000_235427_17f47086 / unit_selfmodel_pilot_42_1000_235468_af0a8a16 | yes |
| unit_selfmodel_pilot_seed42_200t | 9.2 / 9.0 | unit_selfmodel_pilot_42_200_232135_e49d153b / unit_selfmodel_pilot_42_200_232136_1cb49291 | yes |
| unit_selfmodel_pilot_seed456_200t | 8.6 / 8.6 | unit_selfmodel_pilot_456_200_232348_9f35d25a / unit_selfmodel_pilot_456_200_232351_16bbe349 | yes |
| urban_political_seed123_1000t | 172.9 / 183.3 | urban_political_123_1000_225581_176eba88 / urban_political_123_1000_225642_bff896d3 | yes |
| urban_political_seed123_500t | 67.2 / 69.9 | urban_political_123_500_224471_697348b5 / urban_political_123_500_224472_3604eebc | yes |
| urban_political_seed42_1000t | 135.7 / 134.7 | urban_political_42_1000_225430_6290158d / urban_political_42_1000_225487_2eba7ee9 | yes |
| urban_political_seed42_2000t | 175.7 / 173.7 | urban_political_42_2000_239157_d5cd464d / urban_political_42_2000_239163_c61a868e | yes |
| urban_political_seed42_200t | 24.2 / 26.8 | urban_political_42_200_222996_a2739580 / urban_political_42_200_223004_e37bf0c3 | yes |
| urban_political_seed42_500t | 51.6 / 55.0 | urban_political_42_500_224325_641936f3 / urban_political_42_500_224461_20a9eeec | yes |
| urban_political_seed456_1000t | 127.7 / 131.2 | urban_political_456_1000_226185_b08fe63c / urban_political_456_1000_226193_11b50ef5 | yes |
| urban_political_seed456_500t | 45.7 / 48.4 | urban_political_456_500_224672_0bcd2d4e / urban_political_456_500_224740_2bf02c92 | yes |
| urban_political_selfmodel_execution_probe_seed42_200t | 19.4 / 19.4 | urban_political_42_200_240208_47403ce7 / urban_political_42_200_240214_c5c472eb | yes |
| urban_political_selfmodel_probe_seed42_200t | 23.9 / 23.4 | urban_political_42_200_232373_73c361c1 / urban_political_42_200_232388_52bde629 | yes |
| wilderness_survival_seed123_200t | 6.7 / 6.4 | wilderness_survival_123_200_231144_76227bc8 / wilderness_survival_123_200_231176_024e4fe6 | yes |
| wilderness_survival_seed42_200t | 9.9 / 7.1 | wilderness_survival_42_200_231038_bd0909ba / wilderness_survival_42_200_231090_c117444a | yes |
| wilderness_survival_seed456_200t | 6.4 / 6.5 | wilderness_survival_456_200_231211_2a727d37 / wilderness_survival_456_200_231253_18684d11 | yes |

0 non-identical pairs, 0 incomplete, all 162 runs exited 0.

## Result
810 pillar rows; 467 moved (committed anchor not in band of the audit value); 167 more than one grade band away, 300 inside the band but outside the score tolerance; 0 excluded. Moved by pillar: SOCIAL 72, ECONOMY 72, NARRATIVE 65, FACTION 57, PROGRESSION 47, INFORMATION 42, COMBAT 41, WORLD 39, AGENCY 17, COGNITION 15. FACTION is 0.0 on 70 of 81 keys. Against the pre-#536 stage-2 measurement 410 of 810 audit values differ (the move #536 caused), 26 rows moved now that did not before and 44 no longer do.
Columns of `reanchor_table.tsv`: run_key, pillar, committed grade and score, audit grade and score, in_band_before (the committed anchor's own check, grade within +/-1 and score within `max(abs_floor, 20%)`, with its committed per-row overrides, applied to the audit value), in_band_after, moved, excluded.
No stop line is declared for the grade anchors and there is no versioned reference to drift from (rule 10 does not apply to this writer, per the policy table).

## Stage-1 cost sample (measured on the earlier proof SHA dca84e1aa, main 1e42208d0; the cost does not depend on #536) (20 keys; mean of 2 audit runs vs 1 throttled run; load average 10-24)

| run_key | audit s | throttled s | ratio | peak rss MB |
|---|---|---|---|---|
| sandbox_world_seed42_200t | 11 | 9.2 | 1.16 | 93.7 |
| sandbox_world_seed42_1000t | 53 | 46.4 | 1.14 | 114.0 |
| sandbox_world_seed42_2000t | 139 | 116.6 | 1.20 | 113.9 |
| dungeon_crawl_seed42_500t | 21 | 16.7 | 1.24 | 98.1 |
| dungeon_crawl_seed42_2000t | 57 | 50.1 | 1.14 | 99.6 |
| urban_political_seed42_500t | 54 | 47.6 | 1.14 | 153.1 |
| urban_political_seed42_1000t | 144 | 67.7 | 2.12 | 144.1 |
| urban_political_seed42_2000t | 239 | 176.4 | 1.36 | 153.7 |
| simq_routing_test_seed42_500t | 38 | 28.3 | 1.33 | 148.0 |
| simq_routing_test_seed42_1000t | 95 | 70.1 | 1.35 | 163.8 |
| hero_guild_routing_seed42_500t | 47 | 35.1 | 1.34 | 144.9 |
| hero_guild_routing_seed42_1000t | 104 | 70.2 | 1.49 | 144.0 |
| unit_faction_tension_seed42_200t | 9 | 9.1 | 1.01 | 94.5 |
| unit_faction_tension_seed42_2000t | 100 | 78.8 | 1.27 | 118.1 |
| unit_selfmodel_pilot_seed42_1000t | 71 | 60.8 | 1.17 | 118.0 |
| frontier_living_world_seed42_200t | 23 | 20.1 | 1.15 | 139.7 |
| frontier_extended_seed42_200t | 28 | 19.9 | 1.40 | 150.8 |
| generated_frontier_3_42_seed42_1000t | 118 | 73.7 | 1.60 | 162.3 |
| urban_political_selfmodel_probe_seed42_200t | 25 | 20.8 | 1.18 | 145.1 |
| wilderness_survival_seed42_200t | 7 | 6.3 | 1.15 | 126.8 |

Audit/throttled wall ratio: median 1.22, range 1.01-2.12, sum 1.35. Peak disk per run dir: 5 MB (200t), 34 MB (500t), 72 MB (1000t), 59 MB (2000t).

## CI cost estimate
- Slow job: the corpus-diversity step ran 20 min of a 113 min job (run 38127831767, timeout 240 min). Under audit_mode, x1.35 typical (+7 min), x2.1 worst (+22 min); the job stays about 120-135 min. The stability tests also drop from 3 trials to 1, which offsets this.
- `simq-grade-drift` (the only CI producer of anchor reports through `evaluate_simq`) runs the fast tier (<=500t) only, informational, GitHub default timeout; nothing to widen.

## audit_mode validity check (is the move an audit_mode artifact?) (earlier proof SHA dca84e1aa)
Question (testing-planner): FACTION moved down on all 55 moved rows (45 to score 0) while INFORMATION, NARRATIVE and ECONOMY moved up; a one-way move could mean audit_mode changes which systems emit events.

Method: audit vs throttled on the same code, event types and counts from the run dirs; plus the 20-key stage-1 sample.
- **sandbox_world 200t** (audit run `sandbox_world_42_200_3293690_e836f777`, throttled run `sandbox_world_42_200_3293894_50d5f628`): 1290 vs 1294 events; the only event type that differs is `GovernorModeChanged` (1 vs 5). Every pillar is identical in both modes (FACTION C/0.0 with 0 events, ECONOMY S/3.58, NARRATIVE A/0.978, SOCIAL S/6.965). The committed anchors are FACTION S/2.9, ECONOMY B/0.18, NARRATIVE C/0.0.
- **dungeon_crawl 500t and 2000t** (stage 1): FACTION is 0 events / 0.0 in both audit runs and in the throttled run; committed A/1.33 and A/0.58.
- **20-key sample, FACTION event counts, audit vs one throttled run:** equal on 14 keys, audit higher on 2, lower on 4 (urban_political 500t, simq_routing 1000t, hero_guild 500t and 1000t). No systematic direction.
- **INFORMATION up-move, frontier_living_world 200t** (audit `frontier_living_world_42_200_3294877_d4aabb11`; throttled `..._3295074_3958f804` and `..._3295760_b32752b0`): INFORMATION S/58.97 (419 events) under audit vs S/56.45 (398, both throttled runs). The event-type set is identical; only counts differ (cooperation_event 1402 vs about 1810, contract_* and so on), with `GovernorModeChanged` 1 vs 16-17.
- **simq_routing 500t COGNITION:** audit gives 70 events (A, 0.856) on both 500t and 1000t; the throttled runs gave 0 (500t) and 228 (1000t): the host-dependent spread the class-(c) flakes showed, now fixed at one deterministic value.

What audit_mode touches in src (grep of `audit_mode`): `src/engine/signal_source.py:100,185` (zeroed pressure signals, so the governor stays NORMAL); `src/engine/kernel.py:489,614` (overrun and watchdog checks skipped); `:1134` (replay allowed); `:423-448` (fingerprint stability guards); `src/engine/apply.py:317` (transaction trace kept). Already audit_mode: `src/domains/campaigns/runner.py:89`, `src/perf/long_run_harness.py:396`, `src/certification/harness.py`. Nothing in the faction code, `event_extractor.py` or the scorers reads `audit_mode`.

Finding: no audit_mode-only gate in src. audit_mode holds the governor at NORMAL; the throttled run adds a host-dependent governor reaction (mode changes) on top. The committed anchors are stale against main (the fixture was last changed 2026-08-31, #90; test.yml already recorded 61 of 81 drifted), so the one-way FACTION/INFORMATION moves are old drift, in either mode. FACTION = 0 events on dungeon_crawl and sandbox in BOTH modes is an open question for rpg-planner (intended end of the faction chain, or a regression the stale anchors hid).

## Tolerances tightened back (AC4)
Every one absorbed host-speed variance and is back to the shared default (grade +/-1, score `max(0.05, 20%)`), one trial:
- `test_grade_regression.py::SCORE_TOLERANCE_OVERRIDES`: urban_political_seed123_1000t ECONOMY (0.2878), NARRATIVE (0.3197), COGNITION (2.0435), SOCIAL (5.003) and frontier_marches_seed42_200t NARRATIVE (0.3351) removed; the table is empty and a test pins that.
- `test_corpus_diversity.py`: the `band_tolerance=2` override and `abs_floor` 4.482 on urban_political_seed123_500t COGNITION; the evidence-derived `abs_floor` on every other `*_grade_stability` pillar (19 entries); `n_trials` 3 to 1 on 12 tests. The in-test anchor copies are gone: each test reads its anchor from `grade_anchors.json` through `_anchor(run_key, pillar)`, so the two can not drift.
- The three class-(c) COGNITION guards (simq_routing 500t and 1000t, hero_guild 1000t) lose the induced-CPU-load trials and become one audit_mode run against the fixture.

