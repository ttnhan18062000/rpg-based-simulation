---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
phase: open
date: 2026-09-02
tags: [content]
---

# TCK-20260902-WORLDCOMPILER-PLACE-WIRING

## Title
Wire WorldCompiler to construct Places from content

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 2/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, depends on
`TCK-20260902-PLACE-SCHEMA-MIGRATION`. Wires `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`,
confirmed the sole production site constructing a populated `AuthoritativeState` from content) to
construct `PlaceState` instances and populate `RegionState.places`/back-references from
`data/content/world_modules/*.yaml`, replacing today's flat sibling-region model. No world content is
recompiled/migrated yet — that is the pilot tickets' job; this ticket makes the compiler *capable* of
producing the new shape.

## Scope
- Extend `WorldCompiler.compile()` to recognize Place-shaped content and construct `PlaceState`
  instances, linked to their parent `RegionState` via the schema migration ticket's dual-sided
  membership.
- Preserve backward output for any content not yet expressed in Place-shaped form (this ticket wires the
  capability; it does not force-migrate all 21 worlds' content — that is the pilot/rollout tickets).

## Out of Scope
- Recompiling/migrating any specific world (pilot tickets).
- Authoring new Place-shaped content.

## Acceptance Criteria
- [ ] `WorldCompiler.compile()` can construct a correct `PlaceState`/`RegionState.places` pair from
      Place-shaped content, verified by a direct unit test (not just an integration pilot run).
- [ ] Existing (non-Place-shaped) content still compiles unchanged — no regression to current worlds
      until they are explicitly migrated by the pilot tickets.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-PLACE-SCHEMA-MIGRATION (dependency)
- TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT (depends on this)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` item 9

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-WORLDCOMPILER-PLACE-WIRING/`)

## Related Code Areas
- `src/worldbuilding/compiler.py`
- `data/content/world_modules/*.yaml`

## Assumptions / Open Questions
- Whether content authoring needs a schema/format update to express Place-shaped regions, or whether the
  compiler can infer Place boundaries from existing tags — needs a concrete answer during
  implementation, informed by the Stage A world's actual content shape.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
