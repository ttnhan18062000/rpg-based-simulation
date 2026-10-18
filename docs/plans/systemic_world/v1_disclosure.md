---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-10-19"
---

# Baseline v1 disclosure list

**What this is.** Everything that baseline v1 records but does not claim. A row here is a known
property of the v1 world: a rule that never runs, a mechanic that never triggers, a defect whose
fix the owner placed after v1, or a measurement caveat. v1 is honest only together with this list.
The v1 baseline artifact cites this file at the baseline's pinned commit; it does not copy it.

**Who owns it.** rpg-designer owns the wording. rpg-planner supplies the measured inputs. Rows marked
VERBATIM are owner or designer rulings and are not reworded. Every row names its source ruling (memo
row or roadmap item in `owner_decision_memo.md` / `roadmap.md`) and what happens after v1.

**Measured on.** rpg-next 74a310b6e, an ancestor of #645's merged tip 6d7bd1509 (main 3597c08d3); the later commits change no simulation behaviour (type annotations, test isolation, perf inventories, ticket files) unless a row says otherwise: the three gate
worlds (`frontier_living_world`, `urban_political`, `crowded_frontier`), seeds 42-46 (10-seed rows say
42-51), 5,000 ticks, audit_mode.

## M. Measurement caveats

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| M1 | Runs are deterministic only in audit_mode. Outside it, `PhaseBudgetGovernor` reads wall-clock time, so two runs of the same seed can differ. | determinism finding, 2026-10-14 | the pinned governor (real fix) |
| M2 | The cumulative stop base (decision 76) is 903239fbe, the commit just before the first step in the owner's ruled order. Steps 2.120-2.123 were measured and folded before decision 76 existed and are not inside the stop base. They are shown by one report-only reading against c3f6202b9: **TODO (rpg-planner): numbers**. The base predates the typed audit_mode field; its audit is proven by a byte-identical base-vs-base repeat. | decision 76 application, 2026-10-16 | — |
| M3 | The stop line is: cumulative people deaths above 2·SE (SE = per-seed paired-difference SD / √n) and above a floor of 1 per seed per world. Only more deaths stops work; fewer is report-only. A kind counts as base-state only while the step's own parent has it at 0 in every seed. | decision 76 amendments, 2026-10-15/16 | revisit the extinction line at v1 if it keeps firing on noise |

## E. Events and observability (decision 80)

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| E1 | 69 of 138 catalogued event types never fire in the gate worlds. | decision 80 (A) inventory | decision 80 B/C/D |
| E2 | `attrition_threshold_crossed` and `camp_constructed` have no producer. | decision 80 (A) | decision 80 B |
| E3 | Five economy event types the Economy pillar listens for are silent. | decision 80 (A) | decision 80 B |
| E4 | Alert events never reach the event file or SimQ. | decision 80 (A) | decision 80 B |
| E5 | Leadership, clan and betrayal events sit in dead class-level buffers; SimQ's diplomatic input never receives them. | decision 80 (A) | decision 80 B |
| E6 | `biological_state_changed` is CRITICAL on every tick a subject's worst pressure stays at 95 or more, so it floods the stream. The event file is lossless since the event-drop fix, so nothing is lost; the severity is wrong. | event-drop ruling, 2026-10-16 | CRITICAL only on crossing into 95+, WARNING while staying there (decision 80 A) |

## Q. SimQ (decisions 77, 80)

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| Q1 | Three SimQ seeds are grader-shaped content: `faction_tension_overrides`; the pre-queued `pending_information_responses` with the per-world `ENABLE_BELIEF_ASSIMILATION` switch-on; the seeded `pending_self_model_information_events`. | decision 80 (iii), D33 calls 2026-10-16 | three removal steps, each measured alone |
| Q2 | `SIMQ-COGNITION-PIPELINE-WIRE` is off by default and silent: a dead path. | D33 calls 2026-10-16 | judged when a market for information exists (M1) |
| Q3 | SimQ is not graded at v1. Only the ungraded end-to-end data review runs. The live dashboard stream is still sampled under queue pressure, so it depends on host speed; nothing graded reads it. NARRATIVE is retired as a grade. COGNITION and INFORMATION show no-data until milestone 1's typed records exist. | decisions 77, 80 (C/D) | offline grading from the lossless record, then the seven graded pillars |

## C. Combat and terrain

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| C1 | Cover, chokepoints and high ground are built and never trigger in the gate worlds. Cover needs a cover tile between attacker and defender; chokepoints need two blocked tiles opposite across one open tile (the finder runs 116-365 times per world and finds none); high ground needs a fight on mountain, and the only mountain world has no fights. Each is proven by a forced scenario (`tests/unit/combat/test_terrain_mechanics_forced_scenarios.py`). | owner, 2026-10-17 | exercised when a world's geometry first makes them happen |
| C2 | Skill and area attacks (`resolve_skill_usage`, `resolve_aoe_attack`) never fire. If they ran they would bypass the terrain multipliers (precomputed damage; default multipliers). | designer, 2026-10-17 (decision 78) | ONE DAMAGE LAW: every damage path applies the same tactical multipliers through the same call |

## H. World hazards

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| H1 | Subjects do not leave or avoid a draining regional hazard. Slow ground keeps travellers in it longer. Since the route step (2.128), frontier worker deaths shift from combat to hazard (combat 32 → 18, hazard 14 → 21, unattributed hazard 5 → 14), while total frontier worker deaths fall (67 → 59). | decision 75 (b); 2.128 (c) | owed to the owner after v1 |

## S. Social, trust and factions

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| S1 | VERBATIM: "Trust never rises within an episode (its positive writers are unwired). Grief and trust-gated party composition therefore never fire. The other social rules run on bond sentiment, or on a fixed 0.5 trust default that is a constant, not earned trust." | designer, 2026-10-17 | step (ii): trust rises only from real outcome records, never from the per-tick cooperation posture |
| S2 | One abandonment cuts trust every tick until the group dissolves (to -1.0 after about 4 hits, 1-3 ticks apart, 3-56 hits per pair measured on seed 42; grudge to its 5.0 cap after about 17 hits, counted from the code, not measured). Partner fit and group-objective propagation read the result. | owner, 2026-10-18 | step (i): one cut per abandonment episode, as a typed episode record |
| S3 | Rules with no bond to fall back on read trust (stored -1..1) as if it were 0..1. | owner, 2026-10-18 | step (i): one trust scale contract for every reader |
| S4 | Faction pairwise tension never rises within an episode (0.0 in 3 of 4 corpus worlds). | #636 triage, 2026-10-18 | merged into "faction tension from real acts", after the Q1 override removal |

## P. Progression

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| P1 | Combat XP → level-up is correct and rarely reached. frontier: built, reached by 0.4 entities per world (1 of 5 seeds sees any). crowded: built, reached by 0.4 (2 of 5 seeds). urban: never triggers. Nothing passes level 2. Levelling runs through `EvolutionSystem.evaluate` (`src/engine/evolution.py`); the second level-up path is dead (D1-PROG). | #636 triage; Lane A probe 2026-10-19 | XP curve vs kill volume, tuned as a measured step; ONE LEVEL-UP LAW (D1-PROG) |

## D. Dead rules (decision 78)

Name-checked rules whose literal can never equal a content id, so the rule behind them never runs.
From `tools/name_literal_scan.py` (branch rpg-name-scan, bc4ffa63a) run on 74a310b6e: 179 rows in 80
groups. Each is switched on after v1 as its own measured step, with content declaring the property and
code reading no names (decision 56). Limits: the scan is lexical, and the coverage pass is one seed at
2,000 ticks, so a row is a candidate proven dead by that pass, not a proof for every world.

| # | Rule family | Where | Notes |
|---|---|---|---|
| D1 | Recruitment traits GREEDY / CAUTIOUS / LOYAL | `appraisal.py:147-177` | |
| D2 | Combat-stat traits Quick / Strong / Tough | `leveling.py:149-153` | inside the dead level-up path (D1-PROG) |
| D1-PROG | Second level-up path: `LevelingService.process_progression` → `_execute_level_up` | `leveling.py:21-57`, `patches.py:657` | called 0 times in 15 runs; ONE LEVEL-UP LAW after v1: one path, matching `docs/mechanics/attribute_progression_contract.md`, the other removed |
| D3 | Adventure WARRIOR / MAGE | `scoring.py:448` | |
| D4 | WALL line of sight | `legality.py:40, 395-411` | walls are structures (`blocked_tiles`), not terrain |
| D5 | Region-type ecology | `ecology.py:124`, `transformation.py` tables, `camp.py:92`, `reproduction_humanoid.py:70` | |
| D6 | Weather and modifiers | `environment.py:38-115`, `apply_plan.py:331`, `modifier_applicator.py:84` | |
| D7 | World boss | `boss.py:85`, `threat.py:30` | also deferred by the owner (2026-10-05) |
| D8 | Loot, narrative turning points, quest bundle | `loot.py:22`, `narrative.py:46`, `quests.py:242` | |
| D9 | Faction 'default' reputation | `consequence_events.py:138`, `social_memory.py:522` | |
| D10 | Legacy upper-case role maps | `role.py:24-34`, `compiler.py:55-80` | |
| D11 | HERO by name | belief_institution / chronicle / culture / fame, `perception/filter.py:83` | a hero is a person doing adventuring work, not a kind (decision 63) |
| D12 | Region price modifier 'ALL' | `market.py:46` | |
| D13 | rpg_depth PHYSICAL | `rpg_depth.py:349` | |
| D14 | Equipment and world-emergence name checks | `core/equipment.py`, `world_emergence/services.py` | |
| D15 | Species evolution gear by kind name ("goblin", "1"/"2") at levels 10/25/50 | `evolution.py` | never reached: nothing passes level 2 (P1) |
| D-TODO | Four groups still to check row by row: adventure caution/curiosity (`scoring.py:124`, likely a false positive); faction alignment buckets (`faction.py:178`, `hostility.py:53`); navigation TOWN / world_boss (`navigation.py:33`); intelligence 'gold', action_router TRADE | | **TODO (rpg-planner / Lane A)**: walk each; list or drop |

Not listed, by design: the tactical roles VANGUARD / SKIRMISHER / PROTECTOR / SUPPORT / STRIKER are live
(a code enum, not content ids; backlog: should content declare them); the code-held item and recipe
fallback tables are row Y3; schema defaults, harness, observability mode names and the world generator
(no gate world is generated) are not rules.

## Y. Economy (decision 79)

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| Y1 | A tool or trinket with no declared category is `ItemKind.OTHER`, and no shop buys it. Spare weapons and armor sell by kind; declared MATERIAL sells. | decision 79 amendment, 2026-10-15 | a content category, as its own step |
| Y2 | `grass_cover` has base_value 0 in content; it is raised to the market floor of 1. | decision 79 step 2 (2.132) | — |
| Y3 | Code-held fallback items with no catalog entry still exist. | decision 79 step 2 (2.132), decision 78 | removed after v1 |

## K. Kinds

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| K1 | Cave Spider is a scavenger in M0 and is not re-banded. Its data disagree (power small; strength and danger medium; venomous). | decision 53 (Q2), 2026-10-09 | an input to M1's appraisal |
| K2 | Two kinds in an equal power band have no tie rule. | decision 53 (Q2) | M1 gap |

## W. Population and the watch rows (decision 76)

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| W1 | crowded_frontier: blacksmith and guard die out. Blacksmith is base-state (0 in every seed of both arms). Guards go 2 → 0 at the untimed-steps fix (2.126), both in seed 45; accepted. frontier: the raider at 0 is accepted base-state. | owner, 2026-10-16 and 2026-10-18 | the crowded extinction look (decision 78) |
| W2 | crowded_frontier sits AT THE STOP EDGE. Cumulative people deaths 300 → 310 over 10 seeds, equal to the floor, with the per-seed mean +1.00 past 2·SE (0.98). Surviving workers, summed over the 10 seeds, fall 5 → 1 (at the route step alone: alive in 3/10 → 1/10 seeds). | owner, 2026-10-18; 2.128 (a) | the next step that adds crowded deaths past 2·SE stops work as written |
| W3 | crowded_frontier: since the route step, raiders meet workers and scouts more often (raider → worker 35 → 42, raider → scout 16 → 22); total deaths unchanged. | 2.128 (b) | — |
| W4 | frontier workers alive 9 → 21. goblin_warrior and wolf going to 0 in frontier and crowded are the base's post-tick-0 adds, removed by decisions 70 and 79, not deaths. | owner, 2026-10-18 | — |
| W5 | Mortality rises where succession dispatches (since #276): a disclosed behaviour change, not a defect. | roadmap item 2 | parked re-measurement |

## T. Known red tests carried into v1

| # | Disclosure | Source | After v1 |
|---|---|---|---|
| T1 | `test_real_campaign_episode_makes_deliberate_attacks` is a strict xfail: 2 deliberate attacks against 3 required (seed 42, 70 ticks, workers disabled). The assertion is unchanged. | #636 triage; `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-…` | standalone ticket |
| T2 | `test_behavioral_5k` is a known red until the v1 rebaseline. | `TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS` | rebaselined at v1 |

## Open before v1

- M2: the report-only reading's numbers (rpg-planner).
- D-TODO: the four check-per-row groups (rpg-planner / Lane A).
