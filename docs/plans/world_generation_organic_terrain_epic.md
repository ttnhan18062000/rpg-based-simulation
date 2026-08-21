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

**Superseded (2026-08-21) — see "Housekeeping note — resolved" item below.** The "may be dead
code" framing above was itself a false lead: `docs/world/generator_contract.md` and a live P0
parity entry (`SUBSTRATE-NEW-002`) both document `WorldProceduralGenerator` as an intentionally
preserved legacy path, not dead code left over by accident. Decision is to keep it, not delete it —
tracked in `TCK-20260821-PROCEDURAL-GENERATOR-KEPT`.

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

## 2026-08-21 Deeper Investigation

Follow-up pass, read-only, into the world-module system beyond the initial root-cause trace above.
Full detail; corrects two line-number citations above and narrows/refines Scope below.

**Module survey (all 20 real modules under `data/content/world_modules/`, exact counts)**: 3/20
have more than one region — `forest_warden_grove` (2 regions, both `terrain: forest`, edge-adjacent
so they union into one contiguous rectangle, not two components), `nomadic_herd` (2 regions,
`plain`+`forest` — the only multi-region module with >1 distinct terrain), `wolf_den_near_forest` (2
regions, both `terrain: forest`, bounds `[45,10,90,55]` and `[70,30,105,70]` — these **overlap**,
not a clean disjoint pair). 2/20 modules declare zero regions (`forest_deep_ecology`,
`hero_adventurers` — population/resource-only contributions). The remaining 15/20 are strictly
one-region-one-rectangle. Even the 3 modules already attempting multi-part biomes do it by unioning
axis-aligned rectangles of one terrain string — never noise — which independently confirms the root
cause at the content-authoring level, not just the compiler level.

**`WorldModuleSpec`/`ModuleParameterSpec` schema** (`src/worldmodules/schema.py:16-97`) — frozen
Pydantic models, no enum constraint on `RegionRecipeSpec.terrain`/`RegionSpec.terrain` (plain
`Optional[str]` in both `src/worldbuilding/recipe.py:14` and `src/worldbuilding/schema.py:33`), so
heterogeneous per-tile terrain within one region is already schema-legal today — no loosening
needed beyond adding the new noise-fill field. Grepped the entire
`worldgeneration`/`worldbuilding`/`worldassembly`/`worldmodules` tree for "noise|variant|shape|
pattern": zero relevant hits — no existing hook, aspirational or otherwise.

**`ModuleScorer.score()`** (`src/worldgeneration/scorer.py:31-173`) — re-verified line-by-line: pure
function of `intent` fields and static `module.*` attributes, zero `random`/RNG/seed references.
Reconfirms deterministic module *selection* precisely, independent of the prior investigation.

**`WorldModuleRepository`** (`src/worldmodules/repository.py`) — loads via unsorted `os.walk`
(filesystem-order-dependent iteration, though lookup is by `module_id` key so this doesn't affect
correctness); validates each file, raises on duplicate `module_id`. No RNG. Out of this epic's
blast radius.

**Biome-resource validator — resolved open question**: `CatalogValidator._validate_biome_relations()`
(`src/content/validator.py:532-550`) operates only on static catalog-level `biome_id` references
(theme/material/faction), never on compiled per-tile terrain. **Confirmed: needs no change** for the
noise-fill mechanism, since it only ever selects among terrain strings already valid in the catalog.

**Real pipeline, generate → resolve → compile, precisely traced**: `ProceduralCompositionGenerator.
generate()` writes to `data/content/world_compositions/generated/{world_id}.yaml`
(`src/worldgeneration/generator.py:149-153`). A **manual, non-automatic** step then copies/extends
that file into `data/worlds/{world_id}/world.yaml` — confirmed via direct diff against
`generated_frontier_3_42.yaml`, which shows hand-added fields (`faction_tension_overrides`,
`information_source_profiles`, `pending_information_responses`) absent from the generator's raw
output. CLI `resolve` (`src/worldbuilding/cli.py:135-174`) then produces
`data/worlds/{id}/resolved/world.resolved.yaml` + `compile_context.json` via
`WorldAssemblyResolver.assemble()`; CLI `compile` (`cli.py:217+`) consumes those and calls
`WorldCompiler.compile(spec, seed, context)`. **Corrected citation**: the flat-fill loop is at
`src/worldbuilding/compiler.py:205-215` (not 211-221 as first cited) — the real loop also
bounds-clamps to topology width/height and sets `town_tiles` membership from `r_spec.type=="town"`
(independent of terrain), both of which any noise-fill change must preserve.

**New open design question this pass surfaced**: `compile()` instantiates exactly one
`DeterministicRNG(seed)` (`compiler.py` line ~199) shared by the region loop *and* all downstream
entity/resource-placement draws in the same call. A noise-fill mechanism reusing this RNG (as
originally planned) must fix precisely where in that draw sequence it consumes randomness, or
unrelated (non-opted-in) worlds' golden-hash regression tests could shift due to RNG-stream drift.
This is a real sequencing decision, not a detail — Scope item 2 below is updated to call it out
explicitly.

**Test coverage**: `tests/unit/worldbuilding/test_world_compiler.py` (29 tests) has no assertion on
terrain-fill *shape* anywhere; `tests/certification/test_world_compile_determinism.py::
test_compiler_seeding_determinism` only asserts `state_hash` equality across two same-seed compiles.
No existing test locks in flat-fill as a contract beyond overall hash determinism — the new
golden-hash test (Scope item 4) is genuinely new coverage, not a rewrite of anything existing.

**Net effect on scope**: narrows more than it expands. `WorldModuleRepository`, `ModuleScorer`, and
`CatalogValidator._validate_biome_relations()` are all confirmed out of the noise-fill's blast
radius — no child ticket needs to touch them. The one real addition is the RNG-draw-sequencing
decision above, now folded into Scope item 2, plus the `wolf_den_near_forest` region-overlap detail
folded into Scope item 3.

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only. Prospective child tickets:

1. **Extend `RegionRecipeSpec` with an optional noise-fill declaration** (e.g. a
   `terrain_variants: list[TerrainVariantSpec]` or similar field naming TBD) — backward
   compatible: modules that don't declare one keep today's flat single-terrain fill exactly as-is.

   **Update (TCK-20260821-NOISE-FILL-SCHEMA, closed 2026-08-21):** resolved. Added an optional,
   fully inert `terrain_variants: Optional[List[TerrainVariantSpec]]` field to both
   `RegionRecipeSpec` and `RegionSpec`, backed by a single shared `TerrainVariantSpec` model in
   `schema.py` (mirroring the `QuestDefinition` cross-file-sharing precedent), explicitly forwarded
   through `WorldAssemblyResolver.resolve_module_contribution()`. Parity ledger entry `SUB-385`
   added (missing status, not yet verified at that point — see item 2's update below).
2. **Extend `WorldCompiler.compile()`'s region-painting loop** to consult a seeded noise field
   (reusing `DeterministicRNG`, already used elsewhere in this pipeline) when a region declares
   variants, thresholding into per-tile terrain types within the region's existing bounds —
   modeled on Terraria's per-biome noise pass, not a full heightmap rewrite. **Corrected by
   child-ticket investigation (2026-08-21, see `TCK-20260821-COMPILER-NOISE-FILL`)**: the original
   "settle draw-sequence ordering" framing above was based on a misreading of `DeterministicRNG`'s
   real API — it's a stateless composite-key hash (`domain, tick, entity_id, sub_id`), not a
   sequential stream, so draw *order* cannot cause collisions, only key-namespace collisions can. The
   real, simpler requirement: key noise-fill draws under a distinct `Domain` from `Domain.WORLD`
   (e.g. `Domain.INIT`, already registered, confirmed collision-free since `compile()`'s RNG instance
   is distinct from Kernel's own).

   **Update (TCK-20260821-COMPILER-NOISE-FILL, closed 2026-08-21):** resolved. `WorldCompiler.
   compile()`'s region-painting loop now branches on `RegionSpec.terrain_variants`: when populated,
   each in-bounds tile is sampled via `DeterministicRNG.weighted_choice()` keyed under `Domain.INIT`
   (a collision-free 16-bits-per-axis tile-offset encoding, corrected during Review), leaving
   non-declaring regions' flat-fill behavior byte-for-byte unchanged; the existing bounds-clamp and
   `town_tiles` membership rule are untouched in both branches. 10 new tests added (determinism,
   seed-sensitivity, bounds-safety, `Domain.WORLD` isolation, tile-offset injectivity); 163 tests
   across the affected suites pass unmodified. Parity ledger `SUB-385` flipped to `verified`;
   recorded as intentional divergence `2.46` in `docs/guidelines/intentional_divergences.md`.
3. **Update at least one real world module** (e.g. `wolf_den_near_forest`, the FOREST-type module
   the rendering epic's own corpus sweep flagged as the most severe composite-rectangle offender)
   to use the new mechanism, as a real, verifiable proof rather than a purely synthetic test. Its
   two existing regions genuinely overlap (`[45,10,90,55]`, `[70,30,105,70]`) rather than being
   disjoint — the implementation must handle paint-order/overwrite semantics for this case.

   **Update (TCK-20260821-WOLF-DEN-NOISE-MIGRATION, closed 2026-08-22):** resolved. Migrated
   `wolf_den_near_forest.yaml`'s `near_forest` and `wolf_den` regions onto `terrain_variants`
   (`forest` weight=3.0, `swamp` weight=1.0). The intra-module overlap box (`x:[70,90],
   y:[30,55]`) resolves to `wolf_den`'s terrain by an explicit, documented decision — `wolf_den`
   is declared second in `regions:`, so it wins under `WorldCompiler.compile()`'s existing
   declaration-order paint rule (plain dict-key overwrite, no merge/blend) — rather than relying
   on incidental YAML list order, since `wolf_den` carries the higher `hazard_level` (2.0 vs 1.0)
   and is the module's namesake region. Review also surfaced a real, previously-latent
   **cross-module** overlap: in 5 real world compositions that also include
   `bandit_road_trade_pressure` and/or `goblin_camp_conflict` (`frontier_marches`,
   `frontier_extended`, `frontier_living_world`, `lifecycle_full_coverage_world`,
   `simq_scale_stress_seed42`), `near_forest`/`wolf_den` process last under
   `topological_sort_modules()`'s alphabetical tie-break, so tiles inside `bandit_road`'s/
   `goblin_camp`'s own bounds that also fall inside `near_forest`/`wolf_den`'s bounds get
   forest/swamp noise-fill instead of their own module's flat terrain. This pre-dates the
   migration (those tiles were already silently overwritten with flat `"forest"`); confirmed
   cosmetic and legality-inert (`swamp` has no blocking/cover/high-ground effect), not a
   correctness risk, and accepted rather than fixed — see Decision 3b in this ticket's
   `investigation.md` (`staging_artifacts/TCK-20260821-WOLF-DEN-NOISE-MIGRATION/investigation.md`,
   or its `stored_artifacts/` copy after ticket close). 5 new tests added
   (field-preservation, per-tile variation, overlap-winner identity via exact RNG recomputation,
   and bit-identical same-seed recompilation); 234 tests across the scoped verification command
   pass, including every real composition where the cross-module consequence is actually
   exercised. Parity ledger entry `SUB-386` added and `docs/mechanics/06_worldbuilding_foundation.md`
   gained a new "Paint Order for Overlapping Regions" bullet (both out of this doc-updater's own
   scope to re-edit — see those files directly for the authoritative record).
4. **Golden-hash determinism regression test**: same seed still produces bit-identical terrain
   (the noise fill must be seeded and deterministic, not merely "more random").
5. **Housekeeping note — resolved by child-ticket investigation (2026-08-21), NOT a deletion
   candidate**: this item originally asked whether `WorldProceduralGenerator` is safe to delete as
   dead code. Deeper investigation (`TCK-20260821-PROCEDURAL-GENERATOR-KEPT`) found this premise was
   wrong: `docs/world/generator_contract.md` (P1, authoritative) explicitly documents it as the
   intentionally preserved "Spec-based (legacy, preserved)" generation path, and
   `docs/parity_ledger/substrate.yaml` carries a live P0 parity entry (`SUBSTRATE-NEW-002`) asserting
   its determinism. A call-site-only grep methodology for "is X dead code" has now produced this same
   false-lead pattern twice in this codebase's recent history (see also the sibling rendering epic's
   C10 investigation above). The decision is to keep the class, not delete it.

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
- `src/worldbuilding/compiler.py:211-221` — the exact flat-fill loop this epic changes (corrected
  line range, 2026-08-21 pass).
- `src/worldassembly/resolver.py:101,795` — the passthrough this epic's new field must also flow
  through unchanged for modules that don't opt in.
- `src/worldgeneration/generator.py` (`ProceduralCompositionGenerator`, the real live generator)
  vs. `WorldProceduralGenerator` — intentionally preserved legacy path per
  `docs/world/generator_contract.md` and parity entry `SUBSTRATE-NEW-002`, kept not deleted; see
  "Housekeeping note — resolved" above.
- `docs/engine/contracts/regression_and_verification.md` — the Absolute Determinism law this
  epic's noise-fill mechanism must preserve.
- `experiments/spatial_rendering/PROPOSAL.md` §5b/§5c — the original rectangular-biome finding and
  its now-superseded "fix at the noise-blending source" recommendation (correctly revised in that
  document once terrain was found to be spec-fixed, not seed-procedural — this epic is the actual
  follow-up that recommendation was gesturing at).
