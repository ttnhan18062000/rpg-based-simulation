---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
phase: open
date: 2026-09-02
tags: [content, determinism]
---

# TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

## Title
Stage B pilot + remaining-19-world rollout to Region/Place

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 4/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, depends on
`TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT`. Stage B is the first real mixed-content check:
`hero_guild_routing` (4 regions — City + `goblin_camp` wilderness + `ruins_mystery_quest` +
`mountain_pass`) proves the migration handles non-uniform region kinds. Once Stage B is verified by
direct inspection, this ticket also covers migrating the remaining 19 worlds — a staged hard cutover
(no true parallel-run is feasible; `WorldCompiler.compile()` is a single synchronous pass), sequential
world-by-world.

## Scope
- Migrate `hero_guild_routing` to Place-shaped content; compile and verify by direct inspection that all
  4 non-uniform region kinds produce the expected `Place.kind` values.
- Only after Stage B is verified: migrate the remaining 19 worlds' content to Place-shaped form and
  recompile each.
- Recalibration/triage of `state_hash`/`grade_anchors.json` results is this ticket's sibling
  (`TCK-20260902-PLACE-MIGRATION-RECALIBRATION`) — do not fold triage work into this ticket; this ticket
  covers migration + compilation only.

## Out of Scope
- Full state_hash-diff triage and grade-shift analysis across all 21 worlds (separate recalibration
  ticket, sequenced to run alongside/after this one per-world).

## Acceptance Criteria
- [ ] Stage B (`hero_guild_routing`) compiles correctly with all 4 non-uniform region kinds represented
      as the expected `Place.kind` values, verified by direct inspection.
- [ ] Remaining 19 worlds are migrated and recompiled under the new schema.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT (dependency)
- TCK-20260902-PLACE-MIGRATION-RECALIBRATION (runs alongside/after this ticket, per-world)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT/`)

## Related Code Areas
- `data/content/world_modules/hero_guild_routing*.yaml` and the remaining 19 world-module content files
  (exact paths to confirm during implementation)

## Assumptions / Open Questions
This is a genuinely large ticket (20 worlds' worth of content migration) — during implementation, assess
whether it should be split further per-world-batch rather than landed as one PR; note the decision here
if so.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
