---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

`unit_information_source` chosen as Stage A per
`docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2 (two-stage pilot,
recalibration procedure): smallest correctness check, 16 entities, 1 region
(`frontier_village_core` + `hero_adventurers`). No true parallel-run is feasible — `WorldCompiler.compile()`
is a single synchronous pass; the practical equivalent is sequential compile-then-diff against the
already-recorded baseline `state_hash`.
