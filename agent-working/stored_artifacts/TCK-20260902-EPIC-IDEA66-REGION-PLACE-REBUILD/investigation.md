---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD

Scope-only epic. Full investigation is `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
in its entirety — already a complete, field-level, code-verified plan (confirmed against
`RegionSpec.bounds`/`src/worldbuilding/schema.py` and `data/content/world_modules/*.yaml` directly).
Not duplicated here.

Key confirmed facts from that doc, carried forward for this epic's own tracking:
- `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`) is the sole production construction site
  for a populated `AuthoritativeState` — the real insertion point.
- No true parallel-run is feasible for the migration; it must be a staged hard cutover (Stage A → Stage
  B → remaining 19 worlds), using each world's existing `state_hash` as the recalibration baseline.
- The membership-index question (`RegionState.places: List[str]` only, vs. a per-entity `place_id`
  back-reference) is explicitly unresolved and must be decided before any child ticket is cut.
