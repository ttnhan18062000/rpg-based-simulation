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
loop (`src/worldbuilding/compiler.py:205-215`, corrected line range from a 2026-08-21 deeper pass —
see plan doc) flat-fills the entire bounding box with that one terrain string — which mechanically
guarantees a perfect rectangle given rectangular input. This
epic is scope-only: it tracks a breakdown of child tickets, each independently scoped and
investigated when picked up. This ticket does not implement anything itself.

**2026-08-21 deeper investigation** (full report in the plan doc) surveyed all 20 real world
modules, the full `WorldModuleSpec`/`ModuleScorer`/`WorldModuleRepository` machinery, the
biome-resource content validator, and the real generate→resolve→compile pipeline end to end.
Bottom line: confirms the root cause and narrows true scope (no change needed to
`WorldModuleRepository`, `ModuleScorer`, or `CatalogValidator._validate_biome_relations()` — all
verified out of the noise-fill's blast radius) while surfacing one real open design question not
previously called out: `WorldCompiler.compile()` instantiates a single shared `DeterministicRNG`
before the region loop, consumed by later entity/resource-placement draws in the same call — the
noise-fill mechanism must fix exactly where in that draw sequence it consumes randomness, or
golden-hash regression tests for *unrelated, non-opted-in* worlds could shift. See plan doc's
"2026-08-21 Deeper Investigation" section for full detail, including the exact module survey counts
and the `wolf_den_near_forest` region-overlap detail Scope item 3 must account for.

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
   on Terraria's per-biome noise pass, not a full heightmap rewrite. **Corrected by child-ticket
   investigation (2026-08-21)**: the original "settle draw-sequence ordering" framing was based on a
   misreading of `DeterministicRNG`'s real API — it's a stateless composite-key hash
   (`domain, tick, entity_id, sub_id`), not a sequential stream, so draw *order* cannot cause
   collisions, only key-namespace collisions can. The real, simpler requirement: key noise-fill draws
   under a distinct `Domain` from `Domain.WORLD` (e.g. `Domain.INIT`, already registered, confirmed
   collision-free) — see `TCK-20260821-COMPILER-NOISE-FILL`.
3. **Update at least one real world module** (e.g. `wolf_den_near_forest`, the FOREST-type module
   the rendering epic's own corpus sweep flagged as the most severe composite-rectangle offender) to
   use the new mechanism, as a real, verifiable proof rather than a purely synthetic test. Note:
   `wolf_den_near_forest`'s two existing regions (`[45,10,90,55]`, `[70,30,105,70]`) genuinely
   overlap rather than being disjoint — the noise-fill implementation must handle paint-order/
   overwrite semantics for this case, not assume disjoint regions.
4. **Golden-hash determinism regression test**: same seed still produces bit-identical terrain (the
   noise fill must be seeded and deterministic, not merely "more random").
5. **Housekeeping note — resolved by child-ticket investigation (2026-08-21), NOT a deletion
   candidate**: this item originally asked whether `WorldProceduralGenerator`
   (`src/worldgeneration/generator.py`) is safe to delete as dead code (confirmed zero real call
   sites in `src/`/`tools`/CLI this session, only self-referenced by its own unit test). Deeper
   investigation found this premise was wrong: `docs/world/generator_contract.md` (P1, authoritative)
   explicitly documents it as the intentionally preserved "Spec-based (legacy, preserved)" generation
   path, and `docs/parity_ledger/substrate.yaml` carries a live P0 parity entry
   (`SUBSTRATE-NEW-002`) asserting its determinism. A call-site-only grep methodology for "is X dead
   code" has now produced this same false-lead pattern twice in this codebase's recent history (see
   also the sibling rendering epic's C10 investigation, referenced above). `TCK-20260821-PROCEDURAL-GENERATOR-KEPT`
   records this finding and closes the question with a decision to keep the class.

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
- **Child tickets** (created via `/create-tickets`, see `tickets/todos/worldgen-organic-terrain/SEQUENCE.md`
  for implementation order):
- TCK-20260821-NOISE-FILL-SCHEMA
- TCK-20260821-COMPILER-NOISE-FILL
- TCK-20260821-WOLF-DEN-NOISE-MIGRATION
- TCK-20260821-NOISE-FILL-DETERMINISM-TEST
- TCK-20260821-PROCEDURAL-GENERATOR-KEPT — investigation corrected Scope item 5's own "investigate
  whether to delete" framing: `WorldProceduralGenerator` is an intentionally preserved legacy path
  (documented in `docs/world/generator_contract.md`, P1, plus a live P0 parity-ledger entry), not
  dead code. This ticket records that finding and closes the question with a decision to keep it.

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
- `src/worldbuilding/compiler.py:205-215` — `WorldCompiler.compile()`'s flat rectangular-fill loop,
  the exact mechanical cause (corrected line range, 2026-08-21); Scope item 2 changes this. Note the
  real loop also bounds-clamps to topology width/height and sets `town_tiles` membership based on
  `r_spec.type == "town"` (independent of terrain value) — both must be preserved.
- `src/worldassembly/resolver.py:101,795` — `WorldAssemblyResolver`'s passthrough of
  `grid_bounds`/`terrain`, which the new field must also flow through unchanged for modules that
  don't opt in.
- `src/worldgeneration/generator.py` — `ProceduralCompositionGenerator` (the real, live generator;
  sole call site `src/worldbuilding/cli.py:421`) vs. `WorldProceduralGenerator` (confirmed dead
  code, only self-referenced by `tests/unit/worldgeneration/test_generator.py`).
- `data/content/world_modules/*.yaml` — hand-authored `RegionRecipeSpec` content; Scope item 3
  updates at least one real module here (e.g. `wolf_den_near_forest`). 2026-08-21 survey: 20/20
  modules read — 3 have >1 region (`forest_warden_grove`, `nomadic_herd`, `wolf_den_near_forest`),
  only `nomadic_herd` has >1 distinct terrain across its regions; 2 modules have zero regions
  (population/resource-only contributions); the remaining 15 are strictly one-region-one-rectangle.
- `data/content/world_compositions/generated/*.yaml`, `data/worlds/{id}/world.yaml`,
  `data/worlds/{id}/resolved/world.resolved.yaml` — the real pipeline stages between generation and
  compile (2026-08-21 trace): `ProceduralCompositionGenerator.generate()` writes to
  `world_compositions/generated/`; a **manual, non-automatic** copy/extend step produces
  `data/worlds/{id}/world.yaml` (confirmed via diff — the copy adds hand-authored fields like
  `faction_tension_overrides` not in the generator's raw output); `resolve` then produces
  `resolved/world.resolved.yaml` + `compile_context.json`, which `compile` consumes. Any noise-fill
  parameter a module declares must survive this manual copy step (author discipline, not
  code-enforced) to reach a real playable world.
- `src/content/validator.py::CatalogValidator._validate_biome_relations()` — verified 2026-08-21:
  operates only on static catalog-level `biome_id`→theme/material/faction references, never on
  compiled per-tile terrain. **No change needed here** for the noise-fill mechanism, since it only
  ever selects among already-catalog-valid terrain strings.
- `src/platform/rng.py` — `DeterministicRNG`, to be reused (not replaced) for the seeded noise fill.
  2026-08-21 finding: `WorldCompiler.compile()` already instantiates one `DeterministicRNG(seed)`
  shared across the whole compile call (region loop + entity/resource placement) — the noise-fill's
  exact draw-sequence position within that shared stream is an open design decision (see Scope
  item 2).

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

