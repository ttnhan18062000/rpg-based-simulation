---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
phase: open
date: 2026-08-21
tags: [world, determinism]
---

# TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN

## Title
Epic: Seed-Varied, Organic World-Generation Terrain (Root Cause of the Rectangular-Biome Finding)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Make world-generation terrain seed-varied and organic-looking by extending the region/module
pipeline additively — root-causing the "rectangular biome" defect that the sibling rendering epic
(`TCK-20260820-EPIC-WORLD-RENDERING-CORE`) measures via its Shape metric but cannot itself fix. The
root cause is fully traced through live code (not re-investigated here — see
`docs/plans/world_generation_organic_terrain_epic.md` for the complete chain): hand-authored
`RegionRecipeSpec` entries in `data/content/world_modules/*.yaml` declare a single fixed
`terrain: Optional[str]` string per rectangular `grid_bounds`; `ProceduralCompositionGenerator`
selects modules deterministically by intent (never by seed) and seed-samples only each module's
declared numeric/enum parameters, never terrain shape; `WorldAssemblyResolver` passes
`grid_bounds`/`terrain` straight through unchanged; and `WorldCompiler.compile()`'s region-painting
loop (`src/worldbuilding/compiler.py:211-221`) flat-fills the entire bounding box with that one
terrain string — which mechanically guarantees a perfect rectangle given rectangular input. This
epic is scope-only: it tracks a breakdown of child tickets, each independently scoped and
investigated when picked up. This ticket does not implement anything itself.

External precedent (Dwarf Fortress, RimWorld, Terraria, Caves of Qud — full findings in the plan
doc) confirms two things: (1) this project's current fully-fixed-geometry approach is a legitimate,
precedented design point, not simply a bug, and (2) seed-varied terrain and strict determinism are
proven compatible (Dwarf Fortress treats world-gen determinism as an explicit first-class
contract). The recommended path is Terraria's "structured randomness" pattern — keep the region's
`grid_bounds` as a fixed macro-skeleton, vary only the *fill* within it via seeded noise — which
fits this project's real architecture additively, without a rewrite.

## Scope
Prospective child tickets (each independently scoped/investigated later):

1. **Extend `RegionRecipeSpec` with an optional noise-fill declaration** (e.g. a
   `terrain_variants: list[TerrainVariantSpec]` field, exact naming TBD at child-ticket scoping
   time) — backward compatible: modules that don't declare one keep today's flat single-terrain
   fill exactly as-is.
2. **Extend `WorldCompiler.compile()`'s region-painting loop** to consult a seeded noise field
   (reusing `DeterministicRNG`, already used elsewhere in this pipeline) when a region declares
   variants, thresholding into per-tile terrain types within the region's existing bounds — modeled
   on Terraria's per-biome noise pass, not a full heightmap rewrite.
3. **Update at least one real world module** (e.g. `wolf_den_near_forest`, the FOREST-type module
   the rendering epic's own corpus sweep flagged as the most severe composite-rectangle offender)
   to use the new mechanism, as a real, verifiable proof rather than a purely synthetic test.
4. **Golden-hash determinism regression test**: same seed still produces bit-identical terrain (the
   noise fill must be seeded and deterministic, not merely "more random").
5. **Housekeeping note** (likely a small, separate hotfix — not this epic's core work): investigate
   whether `WorldProceduralGenerator` (`src/worldgeneration/generator.py`) is safe to delete as
   dead code (confirmed zero real call sites in `src/`/`tools`/CLI this session, only
   self-referenced by its own unit test), or whether it's intentionally kept for a reason not
   surfaced by this investigation.

## Out of Scope
- **Rewriting the region/module system itself** — this stays additive to `RegionRecipeSpec`, not a
  new world-generation architecture.
- **Changing which modules get selected for a world** — module selection stays deterministic on
  intent, matching the existing, working, and separately-justified design (this is a placement
  question, not a shape question).
- **Any change to `TCK-20260820-EPIC-WORLD-RENDERING-CORE`'s own scope** — that epic and this one
  are related (this one root-causes a finding its `VISUAL-SHAPE-METRIC` child ticket measures) but
  neither is a hard prerequisite for the other, per direct user instruction to treat this as a
  separate epic. The rendering-validation epic can and should proceed independently — it will
  simply keep reporting real, low fill-ratio-adjacent Shape scores against today's content until
  (and unless) this epic's work lands.
- **Resolving `WorldProceduralGenerator`'s dead-code status directly** — noted only as Scope item 5,
  a likely-separate hotfix, not fixed by this epic.

## Acceptance Criteria
Epic tier: no direct implementation acceptance criteria. This epic is considered scoped-complete
when:
- All five Scope items above have corresponding child tickets created and linked back to this
  epic's `ticket_id`.
- Each child ticket, at its own close, demonstrates its own testable acceptance criteria (e.g. the
  golden-hash determinism test in Scope item 4 passing; the updated module in Scope item 3 rendering
  a non-rectangular fill-ratio improvement measurable by the sibling epic's Shape metric).

## Related Tickets
- `TCK-20260820-EPIC-WORLD-RENDERING-CORE` — related but explicitly independent sibling epic (per
  direct user instruction, not a parent/child relationship in either direction). Its
  `VISUAL-SHAPE-METRIC` child ticket (`tickets/todos/world-rendering-core/TCK-20260821-VISUAL-SHAPE-METRIC.md`)
  measures exactly the rectangular-biome symptom this epic root-causes and will fix.

## Related Docs
- `docs/plans/world_generation_organic_terrain_epic.md` — the complete epic plan: full root-cause
  chain, the dead-code correction for `WorldProceduralGenerator`, and the Dwarf
  Fortress/RimWorld/Terraria/Caves of Qud precedent research. Read in full before scoping any child
  ticket from this epic.
- `docs/plans/world_rendering_core_epic.md` — the sibling epic's own plan doc.
- `docs/engine/contracts/regression_and_verification.md` — Absolute Determinism law (Bors Check /
  `TestStrategicRegression::test_headless_run_determinism`); any noise-fill mechanism this epic's
  child tickets add must remain seeded and deterministic under this contract.
- `experiments/spatial_rendering/PROPOSAL.md` §5b/§5c — the original rectangular-biome finding; its
  "fix at the noise-blending source" recommendation was superseded once terrain was found to be
  spec-fixed rather than seed-procedural. This epic is the actual follow-up that recommendation was
  gesturing at.

## Related Stored Artifacts
None found — this is the first investigation in this specific area (`stored_artifacts/` searched
for terrain/world_gen/organic-terrain material, no prior hits).

## Related Code Areas
- `src/worldbuilding/recipe.py` — `RegionRecipeSpec`, the schema Scope item 1 extends.
- `src/worldbuilding/compiler.py:211-221` — `WorldCompiler.compile()`'s flat rectangular-fill loop,
  the exact mechanical cause; Scope item 2 changes this.
- `src/worldassembly/resolver.py:101,795` — `WorldAssemblyResolver`'s passthrough of
  `grid_bounds`/`terrain`, which the new field must also flow through unchanged for modules that
  don't opt in.
- `src/worldgeneration/generator.py` — `ProceduralCompositionGenerator` (the real, live generator;
  sole call site `src/worldbuilding/cli.py:421`) vs. `WorldProceduralGenerator` (confirmed dead
  code, only self-referenced by `tests/unit/worldgeneration/test_generator.py`).
- `data/content/world_modules/*.yaml` — hand-authored `RegionRecipeSpec` content; Scope item 3
  updates at least one real module here (e.g. `wolf_den_near_forest`).
- `src/platform/rng.py` — `DeterministicRNG`, to be reused (not replaced) for the seeded noise fill.

## Assumptions / Open Questions
- Assumes the exact field name/shape for the noise-fill declaration on `RegionRecipeSpec` (e.g.
  `terrain_variants: list[TerrainVariantSpec]`) is TBD and will be settled during Scope item 1's own
  child-ticket scoping/investigation, not fixed by this epic ticket.
- Assumes `layer: world` is correct for this epic (registered value, matches the sibling rendering
  epic's own `layer: world`) — both tickets touch `src/worldbuilding/`/`src/worldassembly/` content
  and generation, not e.g. `rendering`'s presentation-layer concern.
- Assumes the noise-fill mechanism can be made deterministic via `DeterministicRNG` without any
  change to module selection or the region/module schema's core shape — if this assumption proves
  false during Scope item 1/2's own investigation, it would invalidate the "additive, no rewrite"
  framing this epic is scoped around and should be escalated back to this epic ticket before
  proceeding.
- Assumes `WorldProceduralGenerator`'s dead-code status (Scope item 5) genuinely requires no deeper
  investigation than the `grep`-confirmed zero-call-sites finding already in the plan doc; if a real
  reason for keeping it surfaces during that housekeeping ticket, it should be re-scoped as more
  than a hotfix.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

