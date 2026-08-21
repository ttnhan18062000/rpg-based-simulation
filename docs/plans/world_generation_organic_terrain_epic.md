---
status: active
layer: world
authority: P1
audience: agent
tags: [world, determinism]
---

# Epic Plan — Seed-Varied, Organic World-Generation Terrain

**Tracking ticket:** `TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN` (to be created)
**Source:** direct code investigation (2026-08-21) tracing the exact root cause of
`TCK-20260820-EPIC-WORLD-RENDERING-CORE`'s motivating finding, plus external research into
comparable 2D tile-based simulation games' world-generation pipelines.
**Priority:** P1 — root-causes a defect the sibling rendering-validation epic will otherwise keep
finding and re-reporting indefinitely without ever being able to fix it.

## Problem

**The "rectangular biome" finding the rendering epic exists partly to catch is not a bug in any
probabilistic sense — it is the mechanical, guaranteed output of the current pipeline.** Traced
precisely, live-path only (see Corrections below for a dead-code false lead ruled out):

1. Real terrain content is hand-authored as `RegionRecipeSpec` entries
   (`src/worldbuilding/recipe.py`) inside world-module YAML files
   (`data/content/world_modules/*.yaml`, e.g. `frontier_village_core.yaml`:
   `grid_bounds: [10,10,40,40]`, `terrain: "plain"`) — a single terrain string per region, no
   sub-shape or noise field exists anywhere in the schema (`terrain: Optional[str]`, frozen model).
2. `ProceduralCompositionGenerator.generate()` (`src/worldgeneration/generator.py:388`) selects
   *which* modules compose a world — deterministically from intent fields (`danger_level`,
   `settlement_style`, ...), never by seed — and seed-samples only each selected module's
   declared numeric/enum *parameters* (`TCK-20260614-WORLDGEN-SEED-PARAMS`), never terrain shape.
3. `WorldAssemblyResolver` (`src/worldassembly/resolver.py:101,795`) passes each module's
   `RegionRecipeSpec.grid_bounds`/`.terrain` straight through into a `RegionSpec`, unchanged.
4. `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:211-221`) paints terrain with:
   ```python
   for x in range(min_x, max_x + 1):
       for y in range(min_y, max_y + 1):
           terrain[(x, y)] = r_terrain
   ```
   — a flat fill of the region's entire rectangular bounding box with one string. **Given step 1's
   input, this loop cannot produce anything other than a perfect rectangle.** The rendering
   epic's corpus sweep (78.8% of 33 measured components scoring ≥0.95 fill-ratio, zero exceptions
   among non-FOREST types) is this loop working exactly as designed, run repeatedly.

## Correction to prior investigation — a dead-code false lead, ruled out precisely

The sibling rendering epic's own C10 investigation (2026-08-20) examined `WorldProceduralGenerator`
(`src/worldgeneration/generator.py`, the class with `town_center`/`wilderness_forest`/
`wilderness_hills` region carving) and correctly found its terrain-carving code has zero RNG calls.
**That finding is accurate but was investigating unused code**: `grep -rln
"WorldProceduralGenerator"` across the entire live tree returns only `generator.py` itself and its
own dedicated unit test (`tests/unit/worldgeneration/test_generator.py`) — zero real call sites
anywhere in `src/`, `tools/`, or the CLI. The actually-live generator is
`ProceduralCompositionGenerator` (`src/worldbuilding/cli.py:421`, the sole real call site),
confirmed by every real world spec under `data/worlds/*/world.yaml` using
`schema_version: "worldcomposition.v1"` + a `modules:` list, not `WorldProceduralGenerator`'s
output shape. This doesn't change C10's bottom-line conclusion (terrain is genuinely seed-invariant
today) but it changes *where* that's true and *why* — worth a separate, small housekeeping note
(see Related, not scoped as a child ticket here) that `WorldProceduralGenerator` may be dead code
kept alive only by its own test, which is out of this epic's scope to resolve.

## External precedent — how comparable games actually handle this

Researched Dwarf Fortress, RimWorld, Terraria, and Caves of Qud (2026-08-21, full findings in
session notes, not duplicated here). Summary relevant to this epic's design:

- **Not universal**: Caves of Qud — the closest match to this project's "emergent narrative,
  entity-driven simulation" framing — keeps its overworld geography **completely fixed** every
  playthrough by deliberate design, putting procedural budget into content/history instead of
  geometry. This project's current approach is a legitimate, precedented design point, not simply
  a bug to be embarrassed about.
- **RimWorld/Terraria**: terrain shape is genuinely noise-driven per seed from the ground up.
- **Terraria specifically** models "structured randomness": biome *adjacency order* stays
  near-fixed (a macro-layout skeleton), while the *shape* within and around each biome is
  seed-varied via layered noise. This is the pattern that fits this project's real architecture
  without a rewrite: **keep `RegionRecipeSpec.grid_bounds` as the fixed macro-skeleton (matching
  Terraria's fixed adjacency order), but let `WorldCompiler`'s fill step vary the fill *within*
  each region's existing bounds via seeded noise instead of one flat string** — additive to the
  schema, not a replacement of it.
- **Dwarf Fortress** is the one precedent that documents world-generation determinism as an
  explicit, first-class contract (same seed → bit-identical, reproducible, logged for sharing) —
  the same guarantee this project's own `docs/engine/contracts/regression_and_verification.md`
  already requires. Proven compatible with real seed-varied terrain generation, not a novel
  constraint being invented here.

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only. Prospective child tickets:

1. **Extend `RegionRecipeSpec` with an optional noise-fill declaration** (e.g. a
   `terrain_variants: list[TerrainVariantSpec]` or similar field naming TBD) — backward
   compatible: modules that don't declare one keep today's flat single-terrain fill exactly as-is.
2. **Extend `WorldCompiler.compile()`'s region-painting loop** to consult a seeded noise field
   (reusing `DeterministicRNG`, already used elsewhere in this pipeline) when a region declares
   variants, thresholding into per-tile terrain types within the region's existing bounds —
   modeled on Terraria's per-biome noise pass, not a full heightmap rewrite.
3. **Update at least one real world module** (e.g. `wolf_den_near_forest`, the FOREST-type module
   the rendering epic's own corpus sweep flagged as the most severe composite-rectangle offender)
   to use the new mechanism, as a real, verifiable proof rather than a purely synthetic test.
4. **Golden-hash determinism regression test**: same seed still produces bit-identical terrain
   (the noise fill must be seeded and deterministic, not merely "more random").
5. **Housekeeping note** (likely a small hotfix, not part of this epic's core scope): investigate
   whether `WorldProceduralGenerator` is safe to delete as dead code, or whether it's intentionally
   kept for a reason not surfaced by this investigation.

## Out of Scope

- **Rewriting the region/module system itself** — this stays additive to `RegionRecipeSpec`, not
  a new world-generation architecture.
- **Changing which modules get selected for a world** — module selection stays deterministic on
  intent, matching the existing, working, and separately-justified design (this is a placement
  question, not a shape question).
- **Any change to `TCK-20260820-EPIC-WORLD-RENDERING-CORE`'s own scope** — this epic and that one
  are related (this one root-causes a finding the other one's Shape metric will keep surfacing)
  but neither is a hard prerequisite for the other. The rendering-validation epic can and should
  proceed independently — it will simply keep reporting real, low fill-ratio-adjacent scores
  against today's content until (and unless) this epic's work lands.
- **Resolving `WorldProceduralGenerator`'s dead-code status** — noted, not fixed here (see Scope
  item 5's framing as a likely-separate hotfix).

## Related

- `TCK-20260820-EPIC-WORLD-RENDERING-CORE` — sibling epic; its `VISUAL-SHAPE-METRIC` child ticket
  measures exactly the symptom this epic addresses at the root. Cross-reference, not a dependency
  in either direction.
- `src/worldbuilding/recipe.py` (`RegionRecipeSpec`) — the schema this epic extends.
- `src/worldbuilding/compiler.py:211-221` — the exact flat-fill loop this epic changes.
- `src/worldassembly/resolver.py:101,795` — the passthrough this epic's new field must also flow
  through unchanged for modules that don't opt in.
- `src/worldgeneration/generator.py` (`ProceduralCompositionGenerator`, the real live generator)
  vs. `WorldProceduralGenerator` (confirmed dead code, only self-referenced by its own test).
- `docs/engine/contracts/regression_and_verification.md` — the Absolute Determinism law this
  epic's noise-fill mechanism must preserve.
- `experiments/spatial_rendering/PROPOSAL.md` §5b/§5c — the original rectangular-biome finding and
  its now-superseded "fix at the noise-blending source" recommendation (correctly revised in that
  document once terrain was found to be spec-fixed, not seed-procedural — this epic is the actual
  follow-up that recommendation was gesturing at).
