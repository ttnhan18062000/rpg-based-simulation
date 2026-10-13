---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS

## Title
After #536, PROGRESSION reads exactly -0.1569 in 9 different 200-tick grade anchors, and INFORMATION spikes 5-30x in 6 frontier 200-tick anchors. Find out whether each is a real world change or a degenerate signal.

## Status
OPEN (held out of the #531 re-anchor by the rpg-planner ruling of 2026-10-14)

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
From testing-implementer's post-#536 re-anchor table: agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/ruling_table.tsv on branch testing-anchors-audit (#531).
- PROGRESSION goes to C/-0.1569 exactly in:
  - lifecycle_full_coverage_world s42;
  - resource_dense_basin s123;
  - sandbox_world s42, s137 and s999;
  - swamp_border_world s42;
  - unit_faction_tension s42 and s123;
  - wilderness_survival s456;
  all 200t.
- INFORMATION spikes:
  - frontier_extended s456: 0.86 -> 34.98;
  - frontier_living_world s123: 0.2 -> 25.07;
  - frontier_marches s456: 2.1 -> 11.6;
  - generated_frontier_3_42 s123: 2.3 -> 41.8;
  - generated_frontier_3_42 s456: 1.9 -> 17.2;
  - swamp_border_world s456: 8.4 -> 47.5;
  all 200t.

## Scope
1. For each pillar, trace the scorer (src/simulation_quality/) on one affected key at pre-#536 main and at b396080cc. Show which input changes.
   - PROGRESSION: is -0.1569 a floor, a constant from an empty set (e.g. no XP or level events in 200t), or a real measure? Why is it identical across worlds?
   - INFORMATION: does it count #536's new event channels (the starvation record and header, the run-ledger tally, MEAT_DECAYED or FEEDING_KILL), or real information flow?
2. If it's a scorer artifact (it counts observability channels, or degenerates on an empty input), fix the scorer, or route it to the simq owner if it isn't rpg's. Then the rows re-anchor normally.
3. If it's a real world change, write the evidence, and the rows re-anchor under a ruling.
4. Use a revert ablation (#536 minus one cause, in a scratch worktree) only if the trace can't settle it.

## Out of Scope
The other 395 group-A rows (accepted by judgment).

## Acceptance Criteria
- Each of the 15 rows has a measured cause, and is either fixed or re-anchored under a ruling.

## Related Tickets
TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (#531).

## Related Docs
docs/simulation_quality/.

## Related Stored Artifacts
ruling_table.tsv (see above).

## Related Code Areas
src/simulation_quality/ (the PROGRESSION and INFORMATION pillars); src/observability/starvation_record.py; src/observability/run_ledger.py.

## Assumptions / Open Questions
None.

## Implementation Notes
Measured 2026-10-13/14 by rpg-implementer-2, report only (no fix). Method: `tools/calibrate_simq.py --audit-mode` (testing branch's copy, which adds the flag) at pre-#536 (c35ebf475) and post-#536 (b396080cc), 200 ticks, seeds as named; per-event rows from each run's `quality_scores.jsonl`.

PROGRESSION (-0.1569):
- It is `-8 / 51`: the quality report divides a pillar's raw score by `max(effective_tick // 4, last_event_tick)` (`quality_report.py:94-104`; 200t gives a floor of 50). The ONLY PROGRESSION event in these runs is `progression_plateau_detected` type `xp_rate_zero`, which fires once at the first tick past `xp_plateau_by_tick` (50), tick 51, with weight -8. Raw -8, denominator 51: -0.15686. Identical across worlds because nothing else fires: it is the value of "no progression event but the plateau penalty".
- So it is a constant from a near-empty set, not a measure of bad progression: the scorer cannot tell "no XP in 200 ticks" from "bad progression" (the plateau penalty is the only thing that speaks).
- What #536 changed (sandbox_world s42, 200t): pre had 7 PROGRESSION events (`xp_granted` x3, `near_death_survival` x3, the plateau); post has only the plateau. Combat disappeared in the same window: `combat_initiated` 4 -> 0, `near_death_survival` 6 -> 0 (all pillars), `xp_granted` 3 -> 0. XP comes from fights, so with no fight in 200 ticks nothing grants XP. Other changes in the same run: `gold_sink_fired` 62 -> 0 (the gold sink is retired, Ruling 61), `group_joined`/`group_expelled` 58 -> 12/10. Which #536 piece removed the fights (the hostile-list change `relation != NONE`, the AVOID_NO_ROUTE hold, the animals' own ways) is NOT isolated here: that needs a revert ablation.
- Verdict: a real world change (fewer fights in 200 ticks) exposing a scorer that degenerates to a constant on an empty input. testing-planner is right that -0.15686 predates #536 as a committed anchor value for runs with no XP.

INFORMATION (spikes and falls):
- The pillar is almost entirely ONE event type: `decision_diverged_by_belief` at +30 each (`subjective_divergence`). generated_frontier_3_42 s123: post 296 events = 279 divergence events (8370 of 8402 raw points), pre 15 (450). frontier_extended s123: pre 100 divergence events (3000), post 8 (240): the score FELL 14.95 -> 1.13.
- That event is emitted by `event_shapers.py:895-910` on every strategic update of an entity that holds a VAGUE or EXHAUSTED lead while its current project is not an information project. It is a per-entity per-update dwell count, not a discrete happening, so the pillar measures (entities holding a vague lead) x (how often their strategic state updates), times 30. That count swings with any change in who holds vague leads and how long, which is why seeds already differed 53.6 vs 2 before #536.
- The new #536 channels are NOT counted: `starvation_channel_live`/`_tally`, `starvation_death_record`, `rpg_gate_ledger_*` are in no scorer's EVENT_TYPES and appear in no pillar's score rows in these runs (grep: 0). `world_emergence_event` (MEAT_DECAYED, FEEDING_KILL) scores in WORLD, not INFORMATION. So the spike is NOT observability channels.
- Is INFORMATION at 200t a stable measure? No: it is one dwell-dominated event with weight 30, normalised by a denominator of 50..200, so a single entity holding a vague lead for the whole window dominates it.
- Likely fix, for the simq owner: emit `decision_diverged_by_belief` on the transition into the diverged state (or cap per entity per window), or lower its weight; not a #536 regression to revert.

Held rows: 18 frontier-family and swamp_border 200t INFORMATION rows and the 9 PROGRESSION rows; not re-anchored here.

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
