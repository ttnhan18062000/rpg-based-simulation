---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-WOLF-DEN-NOISE-MIGRATION
phase: open
date: 2026-08-21
tags: [world, content, determinism]
---

# TCK-20260821-WOLF-DEN-NOISE-MIGRATION

## Title
Migrate wolf_den_near_forest world module to the noise-fill terrain mechanism

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Update wolf_den_near_forest — the FOREST-type module the rendering epic's corpus sweep flagged as the most severe composite-rectangle offender — to use the new noise-fill mechanism, as a real, verifiable proof of the schema and compiler work. Its two regions (near_forest and wolf_den) genuinely overlap in the box x:[70,90], y:[30,55], so the migration must make an explicit, deliberate decision about paint-order/overwrite semantics instead of relying on incidental YAML list order.

## Scope
- Update wolf_den_near_forest.yaml's two regions (near_forest, wolf_den) to declare terrain_variants (from the schema and compiler tickets).
- Decide and document an explicit overlap-resolution rule for the genuinely overlapping box x:[70,90], y:[30,55] (e.g. last-declared-wins or explicit priority), replacing today's incidental YAML-list-order behavior.
- Select a secondary terrain value for the noise-fill (open assumption — no existing sparse_forest/clearing-style value exists in the real corpus).
- Confirm the migration compiles deterministically (same seed -> bit-identical terrain+state_hash) and that existing load/normalize/resolve pipeline tests for this module keep passing unmodified.

## Out of Scope
- Fixing the unrelated, pre-existing TERRAIN_COST casing bug (src/core/state.py uses uppercase terrain keys while all real module content authors lowercase strings, so movement-cost differentiation is already silently inert for all real content today) — flagged only, not fixed in this ticket.
- Implementing the schema field or the compiler's noise-consumption mechanism — those are hard prerequisites (TCK-20260821-NOISE-FILL-SCHEMA, TCK-20260821-COMPILER-NOISE-FILL), not this ticket's own work.
- Migrating any world module other than wolf_den_near_forest.

## Acceptance Criteria
- [ ] wolf_den_near_forest.yaml's two regions declare the new terrain_variants field with an explicit, documented choice for how the overlap box x:[70,90], y:[30,55] resolves (e.g. last-declared-wins, or explicit priority) — not left to incidental YAML list order.
- [ ] Compiling with a fixed seed produces at least one tile inside each region's bounds whose terrain differs from the region's flat single value pre-migration; tiles outside both regions' bounds are unaffected.
- [ ] Recompiling the same world+seed twice produces a bit-identical terrain dict and state_hash.
- [ ] Existing test_real_content_world_modules.py pipeline tests for this module (load/normalize/resolve) continue passing unmodified.

## Related Tickets
- TCK-20260821-NOISE-FILL-SCHEMA
- TCK-20260821-COMPILER-NOISE-FILL
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260701-HAZARD-KIND-RESOLVER-GAP
- TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE
- TCK-20260701-HAZARD-NATIVE-IMMUNITY
- TCK-20260701-SANDBOX-MONSTER-BALANCE

## Related Docs
- docs/plans/world_generation_organic_terrain_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- data/content/world_modules/wolf_den_near_forest.yaml
- data/content/world_modules/frontier_village_core.yaml
- src/worldbuilding/recipe.py
- src/worldbuilding/compiler.py
- src/worldassembly/resolver.py
- src/core/state.py

## Assumptions / Open Questions
- Secondary terrain type for the noise-fill is an open content-authoring judgment call — no existing value in the real corpus fits 'sub-forest variation' (surveyed: forest x8, plain x5, ruin x2, cave x2, swamp x1, road x1, river x1, mountain x1); 'swamp' is the most plausible reuse candidate (thematically fits a wolf den, already used once elsewhere) but this is not pre-decided by investigation.
- Overlap paint-order resolution (last-declared-wins vs. explicit priority) is genuinely undecided today (incidental YAML order); this ticket must make and document an explicit decision.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
