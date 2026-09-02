---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260902-PLACE-MIGRATION-RECALIBRATION

Every `world_compile_report.json` already carries a `state_hash` field — existing infrastructure, no new
tooling needed for the diff step itself.
`grade_anchors.json`'s tolerance (±1 letter-grade band, `max(0.05, 0.20×score)`) across all 84 committed
`run_keys` is confirmed likely to trip on a structural compile-shape change at this scale even with zero
real gameplay regression, per
`docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`'s own budget note — this is not a
speculative risk, it is the documented expected outcome, hence this ticket's existence as a genuine
per-world triage pass rather than a single batch diff.
