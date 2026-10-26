---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
artifact_type: investigation
phase: done
date: 2026-10-24
tags: [testing, regression, simulation-quality]
---

# Re-anchor provenance: grade anchors on baseline v1

Recorded from runs, never typed (baseline_change_policy.md rules 1-5, 7, 9, 10 and 12). The moved rows are in `reanchor_table.tsv` (all 810 rows, computed by `tools/test_architecture/simq_reanchor.py`) and `ruling_table.tsv` (the 536 moved rows with kind, disposition and cause).

## Cause of this move
- Anchors last re-measured at b396080cc (#531). Window b396080cc..341f700d0: the only src/simulation_quality change is #645's min_events gate (rpg-planner); the world behaviour changed through the v1 steps #645..#720 and was recorded as v1 in #725.
- Ticket: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1. PR: see the commit.

## Owner ruling (rule 5)
- owner_ruling: {ref: "https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6400785924", date: 2026-10-25T17:25:21Z, i.e. 2026-10-26 00:25 +0700} (the owner confirmed rpg-planner's 2026-10-24 ruling).
- Class 1, 322 rows to-no-data: rpg fix (b) min-event rule, #645 (3597c08d3), paired with testing #557; event_count < min_events (3) with reason below_min_events on every one, both reps. Includes the to-no-data rows on the held keys.
- Class 2, 35 NARRATIVE rows: retired under D77, removed by TCK-20261014-SIMQ-PILLARS-COMPUTED-FROM-TYPED-RECORDS-WITH-SEED-SPREAD-D77; not ruled as behaviour.
- Class 3, 36 INFORMATION rows (the 5 S to A grade-downs, the 18 held in #531 included): #645 TCK-20261014-INFORMATION-DIVERGENCE-EVENT-FIRES-ON-ENTERING-THE-DIVERGED-STATE-NOT-EVERY-UPDATE (decision_diverged_by_belief fires once per episode; scorer input changed, formula unchanged); the 18 #531-held rows were stale pre-#531 values.
- Class 4, 107 other rows (per-row causes in `class4_causes.tsv`, copied from rpg-planner's table): cumulative v1 behaviour, #645..#720 (terrain cost as time, D70/D71/D79/D80, #714 v1 fixes); per-row attribution inferred, no regression signal; the owner recorded v1 as the world (#725). Named inferences: swamp_border s123 ECONOMY = terrain time (D75); the 200t PROGRESSION A to B on crowded_frontier / frontier_extended / frontier_living_world = terrain time + #714. The other 5 of the 112 have no disclosed cause (fits=no) and are held.
- HELD, 36 rows (`exclude.tsv`), kept at the committed anchors under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE (rpg): moved non-no-data, non-NARRATIVE rows on hero_guild_routing_seed42_*, simq_routing_test_seed42_* (suspected #645 route_search regression), urban_political_seed456_* (suspected early stall) and wilderness_survival_seed123_200t SOCIAL (cause unknown), plus 5 rows that switched on from 0.0 with no explanation: generated_frontier_3_42_seed42_200t AGENCY, simq_scale_stress_seed42_seed42_200t AGENCY, hero_guild_routing_seed123_500t COGNITION, simq_routing_test_seed123_500t COGNITION, frontier_marches_seed123_200t FACTION. Each key has a slow known-red entry.
- 500 re-anchored + 36 held = 536. `SCORE_TOLERANCE_OVERRIDES` is still empty.

## Proof setup
- Measured sha 341f700d0b54ab00deab0f9b84f87321f101ca48 in a detached worktree; src identical to e8df8b96d (v1 gate run 39799337778 green). See investigation.md for the import proof.
- Producer: `python -m tools.test_architecture.simq_audit_rows --fixture tests/simulation_quality/fixtures/grade_anchors.json --out <dir> --workers 1`, started 2026-10-23 09:49 +07, 162 runs, 0 failed, all pairs identical. Rows: `audit_rows.jsonl`.
- Re-anchor: `python -m tools.test_architecture.simq_reanchor --rows audit_rows.jsonl --fixture grade_anchors.json --out grade_anchors.json --table reanchor_table.tsv --exclude exclude.tsv`.
- Known-reds: the 11 family entries (three family tickets) and the corpus catch-all are retired; 12 entries for the held keys point at the held-rows ticket (expiry 2026-11-15, named by rpg-planner).
- Closed with pointers: TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT, TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE, TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE, TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE.
