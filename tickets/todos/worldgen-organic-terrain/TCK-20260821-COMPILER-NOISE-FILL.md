---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-COMPILER-NOISE-FILL
phase: open
date: 2026-08-21
tags: [world, determinism]
---

# TCK-20260821-COMPILER-NOISE-FILL

## Title
Consume seeded noise in WorldCompiler's region-painting loop for declared terrain variants

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend WorldCompiler.compile()'s region-painting loop to consult a seeded noise field when a region declares terrain variants, thresholding into per-tile terrain types within the region's existing bounds, without letting unrelated worlds' golden hashes shift. The original framing asked to "settle draw-sequence ordering," but investigation found DeterministicRNG is a stateless composite-key hash, not a sequential stream — the real requirement is choosing a collision-free RNG Domain namespace for the new draws. Must preserve existing bounds-clamping and town_tiles membership logic exactly.

## Scope
- Extend WorldCompiler.compile()'s region-painting loop (src/worldbuilding/compiler.py) to consult a seeded noise field when a region's terrain_variants (from TCK-20260821-NOISE-FILL-SCHEMA) is populated, thresholding into per-tile terrain within the region's existing bounds.
- Key noise-fill RNG draws under a distinct Domain from Domain.WORLD (e.g. Domain.INIT, already registered) rather than sequencing within Domain.WORLD's existing entity/resource/building draw order — this replaces the epic's original "settle draw-sequence ordering" framing, since DeterministicRNG is a stateless composite-key hash, not a sequential stream.
- Preserve the existing bounds-clamp and town_tiles membership logic unchanged for both variant-declaring and non-declaring regions.
- Verify unrelated worlds' golden hashes (certification corpus) are unaffected.

## Out of Scope
- Adding the terrain_variants field to RegionRecipeSpec/RegionSpec — that is TCK-20260821-NOISE-FILL-SCHEMA, a hard prerequisite for this ticket.
- Migrating any real world module (e.g. wolf_den_near_forest) to declare variants — that is TCK-20260821-WOLF-DEN-NOISE-MIGRATION.
- Authoring the dedicated golden-hash tile-level regression test — that is TCK-20260821-NOISE-FILL-DETERMINISM-TEST (this ticket only needs to keep the existing determinism tests passing).
- Documentation updates to docs/mechanics/06_worldbuilding_foundation.md, the substrate.yaml parity ledger entry, and docs/guidelines/intentional_divergences.md are required in-session per the Authoritative Mechanics Rule, but are follow-through on this ticket's own change, not a separately deferred scope item.

## Acceptance Criteria
- [ ] Compiling any world spec where no region declares variants produces a bit-identical state_hash and coordinates to pre-change output, verified against the certification corpus.
- [ ] When a region declares variants, compiling twice with the same seed produces identical per-tile terrain assignment within bounds; compiling with different seeds produces a measurably different distribution within the same bounds.
- [ ] Noise-filled terrain never writes outside region bounds or exceeds topology width/height — the existing clamp continues to gate every write.
- [ ] town_tiles membership for a variant-declaring town region is unaffected by which terrain string the noise-fill assigns — still driven solely by r_spec.type == "town".
- [ ] Noise-fill draws are keyed under a distinct RNG Domain (e.g. Domain.INIT) from Domain.WORLD's existing entity/resource/building draws, eliminating collision risk by construction rather than by draw-order sequencing.

## Related Tickets
- TCK-20260821-NOISE-FILL-SCHEMA
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260820-EPIC-WORLD-RENDERING-CORE
- TCK-20260523-WORLD-COMPILER
- TCK-20260619-P0-ENTITY-INIT
- TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md
- docs/parity_ledger/substrate.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/platform/rng.py
- src/worldbuilding/schema.py
- src/worldbuilding/recipe.py
- src/worldassembly/resolver.py
- src/core/enums.py
- tests/unit/worldbuilding/test_world_compiler.py
- tests/certification/test_world_compile_determinism.py
- data/content/world_modules/wolf_den_near_forest.yaml
- data/content/world_modules/forest_warden_grove.yaml

## Assumptions / Open Questions
- Domain.INIT is the recommended noise-fill key namespace per investigation (confirmed registered, confirmed no collision risk since compile()'s RNG instance is distinct from Kernel's own); final confirmation of the exact Domain value happens during implementation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
