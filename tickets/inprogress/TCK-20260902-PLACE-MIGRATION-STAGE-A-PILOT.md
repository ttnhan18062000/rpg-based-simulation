---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
phase: open
date: 2026-09-02
tags: [content, determinism]
---

# TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

## Title
Stage A pilot: migrate unit_information_source to Region/Place

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, depends on
`TCK-20260902-WORLDCOMPILER-PLACE-WIRING`. Smallest correctness check per the plan doc: migrate
`unit_information_source` (16 entities, 1 region — `frontier_village_core` + `hero_adventurers`) so it
compiles as one `Region` containing exactly one `Place(kind=CITY)`. Nothing else should change.

## Scope
- Migrate `unit_information_source`'s content to Place-shaped form.
- Compile it under the new schema and diff `state_hash` against the committed baseline in its
  `world_compile_report.json`.
- A byte-identical hash is the success criterion — anything else must be explained and explicitly
  accepted before Stage B starts, not silently passed through.

## Out of Scope
- Any other world (Stage B and the remaining-19-world rollout are separate tickets).
- `grade_anchors.json` re-runs (only needed if the hash actually changes — see Acceptance Criteria).

## Acceptance Criteria
- [ ] `unit_information_source` compiles as 1 Region containing exactly 1 `Place(kind=CITY)`.
- [ ] `state_hash` is byte-identical to the committed baseline, or the diff is hand-verified,
      explained, and explicitly accepted in this ticket's Completion Summary before Stage B begins.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING (dependency)
- TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT (depends on this)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT/`)

## Related Code Areas
- `data/content/world_modules/unit_information_source*.yaml` (exact path to confirm during
  implementation)

## Assumptions / Open Questions
None beyond what the parent epic already tracks.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
