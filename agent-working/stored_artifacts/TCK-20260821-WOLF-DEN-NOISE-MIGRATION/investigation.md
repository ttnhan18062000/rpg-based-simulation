---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-WOLF-DEN-NOISE-MIGRATION
artifact_type: investigation
tags: [world, content, determinism]
---

# Investigation — TCK-20260821-WOLF-DEN-NOISE-MIGRATION

## Context Scan Performed
1. `search_docs`/its CLI fallback confirmed broken this session by a huggingface.co network block
   (per dispatch note; not retried).
2. `graphify query "wolf_den_near_forest terrain_variants noise fill"` and `graphify query
   "terrain_variants schema compiler noise fill region overlap"` — both returned unrelated
   communities (agent-monitoring retro "Noise Indicators" nodes, `frontend/src/types/api.ts`
   `Region`/`Schema` type nodes). This ticket's own subsystem (world content modules, compiler) is
   not well-represented by these query terms in the current graph snapshot — flagged, not silently
   skipped. `graphify explain "WorldCompiler"` did return the correct node
   (`worldbuilding_compiler_worldcompiler`, `src/worldbuilding/compiler.py:170`, community 297,
   degree 66), confirming the graph itself is current; the two `query` calls were term-mismatches,
   not a stale-index problem.
3. `docs/REGISTRY.yaml` / `tickets/done/` / `stored_artifacts/` for prior work: found and read in
   full `TCK-20260821-NOISE-FILL-SCHEMA` and `TCK-20260821-COMPILER-NOISE-FILL` (both `investigation.md`
   and `COMPILER-NOISE-FILL`'s `plan.md`), plus `tickets/todos/worldgen-organic-terrain/SEQUENCE.md`
   and `docs/plans/world_generation_organic_terrain_epic.md`'s 2026-08-21 deeper-investigation pass.
4. Read every file in Related Code Areas in full, plus `src/worldbuilding/schema.py`,
   `src/engine/rpg_depth.py`, `src/content/resolver.py` (`RegionResolver`),
   `tests/integration/worldassembly/test_real_content_world_modules.py`,
   `tests/integration/content/test_strict_world_matrix.py`,
   `tests/integration/content/test_resource_region_coverage_corpus.py`,
   `tests/integration/content/test_swamp_border_pack.py`,
   `data/content/world_modules/sunken_swamp_border.yaml`,
   `docs/mechanics/06_worldbuilding_foundation.md`, `docs/parity_ledger/substrate.yaml` (`SUB-385`).

## Current Behavior

### `wolf_den_near_forest.yaml` — confirmed exact current content (`data/content/world_modules/wolf_den_near_forest.yaml`, read in full)
Two regions:
- `near_forest`: `type: "wilderness"`, `grid_bounds: [45, 10, 90, 55]` (`[min_x, min_y, max_x, max_y]`
  per `RegionRecipeSpec.grid_bounds`'s own field description and `WorldCompiler.compile()`'s unpack
  `min_x, min_y, max_x, max_y = r_spec.bounds`) → **x:[45,90], y:[10,55]**. `terrain: "forest"`,
  `hazard_level: 1.0`, `hazard_kind: "NATURAL_TERRAIN"`, `tags: [forest]`.
- `wolf_den`: `type: "wilderness"`, `grid_bounds: [70, 30, 105, 70]` → **x:[70,105], y:[30,70]**.
  `terrain: "forest"`, `hazard_level: 2.0`, `hazard_kind: "NATURAL_TERRAIN"`, `tags: [forest]`.

**Overlap arithmetic, done directly (not trusted from the ticket text):**
x-overlap = `[max(45,70), min(90,105)]` = `[70, 90]`. y-overlap = `[max(10,30), min(55,70)]` =
`[30, 55]`. **Confirmed: the ticket's claimed overlap box `x:[70,90], y:[30,55]` is exactly correct.**
This is a real, non-trivial rectangle: 21 × 26 = 546 tiles.

**Fields that must be preserved unchanged by the migration** (both regions): `id`, `type:
"wilderness"`, `hazard_level` (1.0 / 2.0 respectively — deliberately different, do not equalize),
`hazard_kind: "NATURAL_TERRAIN"`, `tags: [forest]`. `terrain: "forest"` (the flat/primary value) is
also preserved unchanged — only a new `terrain_variants` field is added; the existing `terrain` field
continues to serve as `r_spec.terrain`, the flat-fill fallback for any tile the noise draw doesn't
apply to and the value `test_hazard_kind_survives_module_pipeline`/other regression tests never
inspect directly by string but do rely on the region resolving successfully. Also outside this
region: the module also declares `factions`, `populations`, `relationships`, `resources`,
`observability_tags`, and three `quest_definitions` (all `required_location_tags: ["wilderness",
"forest"]`) — none of these reference terrain by string, only by the region-level `tags: [forest]`
label, which this migration does not touch. **Quest routing is therefore unaffected by whatever
per-tile terrain values noise-fill produces**, since routing is tag-based, not per-tile-terrain-based.

### `RegionRecipeSpec`/`RegionSpec`/`terrain_variants` — confirmed already fully live in `main`
`src/worldbuilding/recipe.py:20` and `src/worldbuilding/schema.py:43` both declare
`terrain_variants: Optional[List[TerrainVariantSpec]] = Field(None, ...)`.
`src/worldbuilding/schema.py:27-31`: `TerrainVariantSpec(terrain: str, weight: float = 1.0,
gt=0.0)`, `extra="forbid"`. `src/worldassembly/resolver.py:800` forwards
`terrain_variants=getattr(reg, "terrain_variants", None)` into the resolved `RegionSpec(...)`
construction — confirmed by direct read, ticket #1's schema field and forwarding are real, not
aspirational.

### `WorldCompiler.compile()` region-painting loop — confirmed already fully live (`src/worldbuilding/compiler.py:211-236`, read in full)
```python
for r_spec in spec.regions:
    min_x, min_y, max_x, max_y = r_spec.bounds
    r_terrain = getattr(r_spec, "terrain", "GRASS")
    region_hash = 0
    if r_spec.terrain_variants:
        for ch in r_spec.id:
            region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:
                if r_spec.terrain_variants:
                    tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)
                    entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF
                    tile_terrain = rng.weighted_choice(
                        Domain.INIT, tick=0, entity_id=entity_id,
                        seq=[v.terrain for v in r_spec.terrain_variants],
                        weights=[v.weight for v in r_spec.terrain_variants],
                        sub_id=1,
                    )
                else:
                    tile_terrain = r_terrain
                terrain[(x, y)] = tile_terrain
                if r_spec.type == "town":
                    town_tiles.add((x, y))
    regions[r_spec.id] = RegionState(... bounds=r_spec.bounds, kind=r_spec.type.upper(),
        hazard_level=..., hazard_kind=... )
```
`SUB-385` in `docs/parity_ledger/substrate.yaml` (lines 4806-4824) is already `status: verified`
with real `v2_evidence`/`test_path`. The Mechanics Bible's `### Noise-Fill Terrain Law` subsection
(`docs/mechanics/06_worldbuilding_foundation.md:34-39`) and `docs/guidelines/intentional_divergences.md`
`### 2.46` are both already landed. **This ticket's own prerequisites are genuinely done, not
just claimed done** — verified by direct read, not by trusting ticket status fields.

### Overlap-resolution mechanism — confirmed by direct read of the loop above
`spec.regions` is iterated as a plain Python list, in declaration order. `terrain[(x,y)] = ...` is a
**plain dict-key overwrite** — no merge, no max/priority logic. For any tile `(x,y)` that falls
inside more than one region's bounds, **whichever region is later in `spec.regions` overwrites
whichever region processed earlier**, unconditionally — this is true today (pre-migration, both
regions write the identical flat string `"forest"`, so the overwrite is currently invisible) and
remains true post-migration (each region's own noise draw, if declared, will be independently
computed for the same `(x,y)` tile — the earlier region's draw is fully computed and then discarded,
never merged or blended).

**Region declaration order for this module is fixed and confirmed**: `near_forest` is listed first,
`wolf_den` second, in `wolf_den_near_forest.yaml`'s own `regions:` list. Tracing this order forward:
`WorldModuleAuthoringNormalizer.normalize()` does `regions=list(spec.regions)` (pure passthrough,
confirmed by ticket #1's investigation and re-confirmed here — no reordering). `WorldAssemblyResolver
.resolve_module_contribution()`'s region loop (`resolver.py:785-801`) iterates
`normalized_module.regions` in order and `.append()`s to `regions_spec_list` — again no reordering.
Since both `near_forest` and `wolf_den` are declared by the *same* module (no other module in this
world composition declares either region), their relative order in the final `WorldSpec.regions` list
used by `compile()` is determined solely by this module's own YAML list order, unless assembly-order
DAG resolution (Kahn's topological sort, Mechanics Bible §4) reorders modules — but region order
*within* one module's contribution is not something the DAG sort touches (it sorts module/dependency
nodes, not the region list inside a single module's contribution). **Conclusion, directly verified,
not assumed: `wolf_den` is processed after `near_forest` at compile time today, and will continue to
be, as long as the YAML list order is not changed.**

### Overlap Policy — confirmed unenforced (a real, pre-existing, un-flagged gap this ticket's own AC exposes)
`docs/mechanics/06_worldbuilding_foundation.md:32` states as law: *"By default, regional bounds are
strictly disjoint (no overlapping). This is enforced unless `allow_overlapping_regions` is explicitly
enabled in the validation spec."* Grepped `src/worldassembly/`, `src/worldbuilding/`,
`src/worldmodules/` for `allow_overlapping_regions`/`overlap`: the **only** hit in all of `src/` is
the field's own declaration, `ValidationSpec.allow_overlapping_regions: bool = Field(False, ...)`
(`src/worldbuilding/schema.py:193`). **No code anywhere reads this field to actually reject
overlapping region bounds.** `RegionResolver.resolve()` (`src/content/resolver.py:639-643`) only
checks that the region *id* exists in the catalog — no bounds/geometry check at all. Confirmed via
every real resolved world's `world.resolved.yaml` (`frontier_marches`, `swamp_border_world`,
`sandbox_world`, 15+ others, grepped directly): every single one has `allow_overlapping_regions:
false`, and `wolf_den_near_forest`'s two genuinely-overlapping regions compile into several of them
today (e.g. `frontier_marches`, `swamp_border_world`) without error. **This is a real Mechanics
Bible / code parity gap that predates this ticket** — the "Overlap Policy" law is aspirational
documentation, not enforced behavior, today. This ticket does not introduce the gap and fixing
enforcement is out of this ticket's scope (would need a real validator, would need to decide whether
to reject or retroactively flip `allow_overlapping_regions` for every affected world, and would touch
content far beyond `wolf_den_near_forest.yaml`) — but it is the reason today's overlap has never
caused a validation failure, and it directly explains why this ticket is free to migrate
`wolf_den_near_forest.yaml` without first resolving that separate gap. Flagged in Risks below as a
worthwhile follow-up ticket, not blocking this one.

### `legality.py` terrain semantics — confirmed exhaustively (`src/engine/legality.py`, grepped and read the 5 relevant blocks)
- Movement/LoS blocking: only `"WALL"` (line ~72, ~385, ~401).
- High ground (`check_high_ground`, lines 416-424): `{"HILL", "MOUNTAIN"}`.
- Cover (lines 487, 492): `{"WALL", "FOREST", "MOUNTAIN"}`.
- **`"SWAMP"` appears nowhere in `legality.py`** — no blocking, no high-ground, no cover semantics.
  It is tactically inert at the legality layer, exactly like `"PLAIN"`/`"GRASS"`/`"ROAD"`/`"CAVE"`/
  `"RUIN"`/`"SAND"` (none of which appear in `legality.py` either).

### `TERRAIN_COST` casing bug — confirmed real (ticket's Out-of-Scope claim independently verified)
`src/core/state.py:344-354`: `TERRAIN_COST` dict keys are uppercase (`"ROAD"`, `"PLAIN"`, `"FOREST"`,
`"SWAMP"`: 3.0, `"HILL"`, `"MOUNTAIN"`, `"SAND"`). Sole consumer:
`TerrainCostService.get_tile_cost()` (`src/engine/rpg_depth.py:290-300`):
`terrain_type = terrain.get(pos, "PLAIN")` (reads the raw `state.terrain` dict value, whatever case
it was authored in) then `TERRAIN_COST.get(terrain_type, 1.0)`. Every real module in
`data/content/world_modules/` authors `terrain:` as a **lowercase** string (`"forest"`, `"swamp"`,
`"plain"`, `"cave"`, `"ruin"`, ...; confirmed for `wolf_den_near_forest.yaml`,
`sunken_swamp_border.yaml`, `frontier_village_core.yaml`, all read directly above). A lowercase
`"swamp"` lookup against the uppercase-keyed `TERRAIN_COST` dict misses and silently falls back to
the `1.0` default — **no real content today gets any terrain-cost differentiation at all**,
confirmed exactly as the ticket's Out-of-Scope section states. Authoring `terrain_variants` with a
`"swamp"` (or any lowercase) secondary value does not trigger or interact with this bug in any new
way — it is exactly as inert as the module's existing `terrain: "forest"` value already is. Correctly
out of scope; **do not fix this as part of this ticket** (confirmed, not just repeated from the
ticket text).

### `frontier_village_core.yaml` — confirmed genuinely relevant, no changes needed
Listed in Related Code Areas because `wolf_den_near_forest.yaml` declares `requires:
["frontier_village_core"]` (line 6) and both modules' factions/relationships
(`town_to_wild_beasts`/`wild_beasts_to_town`) are cross-referential — it is real dependency context,
not incidental. Its one region, `hometown`, has `grid_bounds: [10, 10, 40, 40]` → x:[10,40], y:[10,40]
— **does not overlap** either `near_forest` ([45,90]×[10,55]) or `wolf_den` ([70,105]×[30,70])
(gap of 5 tiles in x between `hometown`'s max_x=40 and `near_forest`'s min_x=45). `terrain: "plain"`,
`tags: [plain, settlement]`. **No change required to this file** — the Scope section's silence on it
is correct; it is comparison/dependency context only. It also independently corroborates the "plain"
terrain candidate's real-corpus meaning: `hometown` uses `"plain"` for a settled town center, which is
a thematic mismatch for a wilderness wolf-den region's secondary terrain (see Decision 2 below).

### Test regression surface — confirmed by direct read of `MODULE_MATRIX` and every test body
`tests/integration/worldassembly/test_real_content_world_modules.py`'s `MODULE_MATRIX` (line 10-34)
includes `"wolf_den_near_forest"` (line 12) and `"frontier_village_core"` (line 11). Tests iterating
`MODULE_MATRIX` that touch this module: `test_real_world_modules_load_from_data_content` (schema
validity + `module_id`), `test_real_world_modules_normalize` (clean normalize), 
`test_real_world_modules_preserve_count_maps` (region/population/resource/building counts —
**counts only, never terrain string content**), `test_real_world_modules_resolve_contributions`
(region/population/resource/building counts again), `test_real_world_modules_reference_graph_edges_exist`
(population/resource/building catalog-reference validity — terrain-independent). Additionally,
`test_hazard_kind_survives_module_pipeline` (lines 113-143) asserts `wolf_den_near_forest`'s two
regions' `hazard_kind` is exactly `{"near_forest": "NATURAL_TERRAIN", "wolf_den": "NATURAL_TERRAIN"}`
end-to-end through normalize→resolve — this is the load-bearing reason `hazard_kind` must not be
touched by the migration. `test_terrain_variants_survive_module_pipeline` (lines 146-191) exercises
the field's pipeline survival via a **synthetic** module, not `wolf_den_near_forest` — unaffected by
this migration either way, but establishes the exact assertion pattern
(`{r.id: r.terrain_variants for r in ...regions}`) usable for a new wolf_den-specific test.
**None of these tests inspect `terrain`/`terrain_variants` string values for `wolf_den_near_forest`
specifically** — only counts and `hazard_kind`. Since this migration adds `terrain_variants` (a new,
previously-`None` field) without changing `type`/`hazard_level`/`hazard_kind`/`tags`/`terrain`,
**every one of these tests keeps passing unmodified**, confirmed by tracing each assertion, not by
assumption.

Also confirmed relevant but unaffected by content changes (structural/assembly-level, terrain-blind):
`tests/integration/content/test_strict_world_matrix.py` (`_MATRIX`, asserts no blocking assembly
errors for compositions including `wolf_den_near_forest`), `test_resource_region_coverage_corpus.py`
(`_ACCEPTED_ZERO_CONTENT_REGIONS` includes `"wolf_den"` by design, per
`intentional_divergences.md#2.29` — resource-coverage exemption, terrain-unrelated),
`test_swamp_border_pack.py` (assembly success only, for compositions combining
`wolf_den_near_forest` + `sunken_swamp_border` — a real precedent for these two "wolf"/"swamp" themed
modules already coexisting in the same world without conflict).

## Mechanics / Engine Constraints
- `docs/mechanics/06_worldbuilding_foundation.md` §2 "Regional Boundaries & Sovereignty" — `Spatial
  Laws`: bounds format `[min_x,min_y,max_x,max_y]` (confirmed matches this module exactly),
  `min<=max` validity (both regions satisfy this — `RegionRecipeSpec.validate_bounds()` would already
  reject them otherwise), `Topology Alignment` (region bounds within topology dims — enforced today
  via `compile()`'s own clamp, not by the region spec itself; not this ticket's concern), and
  `Overlap Policy` (aspirational/unenforced, see Current Behavior above — this ticket's migration
  operates within a pre-existing, undocumented-as-such gap, not one it creates).
- `### Noise-Fill Terrain Law` (same file, lines 34-39, added by ticket #2) — already fully describes
  the per-tile weighted-sampling behavior this migration will exercise for real content the first
  time; describes variant-declaring vs non-declaring behavior generically but says nothing about
  *overlapping* variant-declaring regions specifically (silent on paint-order for overlaps) — see
  Decision 3 and Docs Requiring Update below.
- `docs/core/state.md` immutability law: `RegionRecipeSpec`/`RegionSpec`/`TerrainVariantSpec` are all
  `frozen=True`; this migration only adds YAML content (data), not code, so it does not touch this
  law at all.

## Docs Requiring Update
- `docs/mechanics/06_worldbuilding_foundation.md`: the `### Noise-Fill Terrain Law` subsection
  (lines 34-39) documents variant-declaring vs non-declaring behavior generically but is silent on
  what happens when two variant-declaring regions overlap. Add one bullet under that subsection
  stating the compiler's actual, confirmed-by-code behavior: for any tile inside more than one
  region's bounds, the region later in `WorldSpec.regions` declaration order overwrites the terrain
  (flat or noise-sampled) of any region processed earlier for that tile — no merge/blend. This is the
  first real-content case this law becomes operationally visible for (pre-migration, both
  `wolf_den_near_forest` regions wrote the same flat `"forest"` string, so the overwrite was
  invisible); the doc should describe the general mechanism, not name this specific module.
- `docs/parity_ledger/substrate.yaml`: `SUB-385`'s existing text describes the compiler mechanism
  generically and does not reference any real content module using it. Add a **new** entry (next
  available `SUB-3XX` id) documenting that `wolf_den_near_forest.yaml` is the first real content
  module to declare `terrain_variants` in production, `status: verified`, `v2_evidence` citing the
  YAML file itself plus `terrain_variants` field values, `test_path` citing the new wolf_den-specific
  determinism/content test (see test_plan.md). This is a genuinely new fact (real content now
  exercises the mechanism) distinct from `SUB-385`'s own schema/compiler-mechanism claim — do not
  overload `SUB-385` itself with this module-specific claim.
- `data/content/world_modules/wolf_den_near_forest.yaml` itself is not a `docs/` path, but per the
  Overlap-resolution decision below, add a YAML comment (not a schema field — none exists for
  authoring-time overlap-priority intent) directly above the `regions:` list or above the `wolf_den`
  entry, stating explicitly that `wolf_den` is declared after `near_forest` deliberately, so that its
  terrain (flat or noise) wins the shared tile box `x:[70,90], y:[30,55]` per the compiler's
  declaration-order paint rule — turning today's incidental order into a documented, intentional
  choice as the ticket's AC requires. (Recorded here as a required content-authoring change, not a
  `docs/` path, so it does not appear in the bullet list below, which is `docs/`-scoped per the
  required format — but Plan must not drop it.) **Extended per Decision 3b (added post-Review)**: the
  same comment must also cover the cross-module overlap this migration makes newly visible
  (`bandit_road_trade_pressure`/`goblin_camp_conflict` in 5 real compositions) — see Decision 3b for
  the exact facts to include.

## Parity Ledger Overlap
- `SUB-385` (`docs/parity_ledger/substrate.yaml`, lines ~4806-4824): `status: verified`, `priority:
  P2`. Already covers the schema+compiler mechanism generically. This ticket's migration is a new,
  narrower fact (first real content usage) that should get its own entry rather than mutating
  `SUB-385`'s existing verified text (see Docs Requiring Update). Not a P0 entry — no `test_path`
  is strictly mandatory by ledger rules for P2, but per repo convention (`SUB-385` itself, and
  `TCK-20260821-COMPILER-NOISE-FILL`'s own precedent) a real `test_path` should still be supplied.
- No other parity ledger entry references `wolf_den_near_forest` by name (grepped
  `docs/parity_ledger/*.yaml` for `wolf_den`/`near_forest`: no hits outside the two hazard_kind-era
  test-path citations already covered by `SUB-385`'s sibling entries, not re-quoted here since they
  are unaffected by this ticket).

## Prior Work
- `TCK-20260821-NOISE-FILL-SCHEMA` (done) — added the inert `terrain_variants` field. Investigation
  confirmed the field/model shape this ticket's YAML must conform to (`terrain: str`, `weight: float
  = 1.0, gt=0.0`).
- `TCK-20260821-COMPILER-NOISE-FILL` (done) — made the field consequential. Investigation established
  (a) `DeterministicRNG` is a stateless composite-key hash, no sequential stream, so authoring
  `terrain_variants` cannot perturb any other region's or entity's RNG draws regardless of value
  count/weights; (b) `state_hash`/`StateFingerprinter` structurally excludes `state.terrain` — hash
  equality alone can never prove or disprove a terrain-painting change, direct `state.terrain`
  dict-content assertions are required (directly relevant to this ticket's own AC #2/#3, see
  test_plan.md); (c) explicitly flagged, as a forward-looking risk for *this* ticket, that
  `legality.py` gives real tactical meaning to `WALL`/`FOREST`/`MOUNTAIN`/`HILL` and that `compile()`
  never checks terrain-type legality at spawn time — directly informs Decision 2 below (prefer a
  legality-inert secondary terrain).
- `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (done) — established
  `test_hazard_kind_survives_module_pipeline` as the exact regression test this migration must not
  break; confirms the field-preservation discipline (`hazard_kind`/`tags`/`hazard_level` must survive
  the pipeline unchanged) this migration must also uphold for its own new field.
- `docs/plans/world_generation_organic_terrain_epic.md`'s "2026-08-21 Deeper Investigation" section
  independently surveyed the full real-content corpus and reached the same overlap finding
  (`x:[70,90],y:[30,55]`, un-re-derived there, only asserted) that this investigation re-derives from
  arithmetic directly — consistent, not contradictory.

## Risks and Open Questions

### Decision 1 (bounds/fields) — RESOLVED, no open question
Confirmed by direct read and arithmetic above: bounds, overlap box, and all fields-to-preserve are
exactly as the ticket claims. No discrepancy found.

### Decision 2 (secondary terrain value) — RESOLVED: **`swamp`**
Reasoning, evidence-backed:
- **(a) Legality semantics**: `SWAMP` has zero special handling in `src/engine/legality.py` — no
  blocking, no cover, no high-ground. This is a *positive* property for this migration, not a
  weakness: `TCK-20260821-COMPILER-NOISE-FILL`'s own investigation explicitly flagged that
  `compile()` never checks terrain-type legality at spawn/placement time, so choosing a
  tactically-loaded terrain (`WALL`, `MOUNTAIN`, `HILL`, `FOREST`-as-cover) as the noise-fill
  secondary value risks silently stranding an already-placed entity on impassable/high-ground terrain
  with no compile-time guard. `SWAMP` (like `PLAIN`/`ROAD`/`CAVE`/`RUIN`/`SAND`, all also absent from
  `legality.py`) carries no such risk. `TERRAIN_COST["SWAMP"] = 3.0` (`src/core/state.py:350`) is the
  only place `SWAMP` has any differentiated meaning at all, and that lookup is confirmed dead for all
  real content today (casing bug, see above) — so choosing `swamp` has **zero live gameplay effect
  today**, and if the casing bug is ever fixed later, `SWAMP`'s higher movement cost (3.0 vs
  `FOREST`'s 1.5) becomes a *thematically appropriate* dividend (marshy/rough den terrain being harder
  to move through), not a regression to guard against.
- **(b) Real corpus precedent**: `swamp` is used exactly once today,
  `sunken_swamp_border.yaml`'s `swamp_border_territory` region (`type: "wilderness"`, `hazard_level:
  2.5`, `hazard_kind: "NATURAL_TERRAIN"` — the same `type`/`hazard_kind` shape as both
  `wolf_den_near_forest` regions). `test_swamp_border_pack.py` already exercises
  `wolf_den_near_forest` + `sunken_swamp_border` coexisting in the same world composition without
  conflict, a real precedent for these two wilderness-flavored modules sharing thematic space.
  Reusing `swamp` keeps within the established, catalog-valid content vocabulary rather than
  inventing an unprecedented string, honoring the ticket's own framing ("no existing
  sparse_forest/clearing-style value exists — must reuse").
- **(c) Alternatives ruled out**: `cave` is used exclusively for architecturally-distinct
  mine/cult-cave regions (`old_mine_resource_loop`'s `old_mine`, `moon_cult_ruins`' `moon_cave`) — an
  underground/excavated theme, not an outdoor wolf-den-in-forest theme. `ruin` is used exclusively for
  structure/architecture-themed regions (`ruins_mystery_quest`, `undead_battlefield`) — again a poor
  fit for an animal ecology module. `plain` (5 uses, including `frontier_village_core`'s own
  `hometown`, `tags: [plain, settlement]`) reads as settled/civilized terrain — the opposite
  connotation from a wolf den's rough wilderness, and would blur thematic distinction from the
  adjacent town region. `road`/`river`/`mountain` (1 use each) are all worse fits: a road implies
  maintained infrastructure inconsistent with wilderness; a river/mountain each carry strong
  standalone geographic identity that doesn't read as "sub-forest variation" the way a marshy
  undergrowth patch does. **`swamp` is confirmed the best available real-corpus fit, not merely the
  least-bad option** — it is the only single-use candidate whose existing thematic context
  (wilderness/lizardfolk-adjacent bordering region) is genuinely close to "rough wild terrain
  bordering a settlement," the same shape `wolf_den_near_forest` itself occupies.
- **Recommended weight**: a forest-dominant ratio (e.g. `forest: weight=3.0`, `swamp: weight=1.0`,
  i.e. ~75%/25%) is recommended so noise-fill visibly diversifies the terrain (satisfying AC #2's "at
  least one tile differs" requirement with high statistical confidence given the region sizes — 2116
  tiles for `near_forest`, 1476 for `wolf_den`, minus their 546-tile overlap) while keeping "forest"
  as the region's dominant, recognizable character. This is a Plan-level parameter choice, not
  re-litigated further here; the investigation confirms both the mechanism (`weighted_choice`, true
  relative weighting, confirmed at `src/platform/rng.py:100-103`) and the corpus-size math support any
  ratio that isn't near-0%/near-100%.

### Decision 3 (overlap resolution) — RESOLVED: **document declared order as the deliberate choice; do not reorder or add new mechanism**
Confirmed by direct trace above: today's (and post-migration's) actual behavior is **last-declared-in-
`spec.regions`-wins**, i.e. `wolf_den` (declared second in the YAML) overwrites `near_forest`'s tiles
in the shared box. Two sub-questions resolved:
1. **Should the declared order be changed (i.e. should `near_forest` instead be declared after
   `wolf_den` so it wins)?** No. Recommend **keeping wolf_den second** (current order), because it is
   thematically coherent: `wolf_den` has the higher `hazard_level` (2.0 vs 1.0) and is the module's
   namesake "core" region; the shared tile box being painted with `wolf_den`'s character (whether
   flat "forest" pre-migration, or noise-sampled forest/swamp post-migration) matches the narrative
   logic that the overlap zone is "close enough to the den to count as the den's territory," not
   merely "near the forest." Reversing the order would make the more dangerous, named region's
   terrain get silently discarded in its own overlap box — a worse outcome, not a neutral one.
2. **Is a schema-level explicit-priority mechanism needed instead of order-dependence?** No such
   mechanism exists today (`RegionRecipeSpec` has no priority/precedence field, and adding one would
   be a schema change — out of this ticket's scope, and out of scope for both closed prerequisite
   tickets too). The ticket's own Scope explicitly offers "e.g. last-declared-wins or explicit
   priority" as alternatives; **last-declared-wins is the correct, sufficient choice** because it (a)
   requires no new code (this ticket is content-only per its own Out of Scope), (b) is what the
   compiler already and unavoidably does today, and (c) produces the thematically better outcome per
   point 1. The only real gap is that this order has never been *documented* as intentional — this
   ticket closes that gap via (i) a YAML comment in `wolf_den_near_forest.yaml` stating the choice
   explicitly (see Docs Requiring Update) and (ii) a generic paint-order bullet added to the Mechanics
   Bible's Noise-Fill Terrain Law subsection (also see Docs Requiring Update), which documents the
   *mechanism* for any future overlapping-region content, not just this module.

### Decision 3b (added post-Review) — Cross-module overlap survey and its own explicit resolution

**Gap in the original investigation, found and fixed during Review**: Decision 3 above only surveyed
overlaps *within* `wolf_den_near_forest.yaml` (near_forest↔wolf_den) and against
`frontier_village_core`'s `hometown`. It never surveyed the real, currently-shipping world
compositions this module actually ships in for *other modules'* region bounds overlapping
`near_forest`/`wolf_den`. Review found two real overlaps by checking every real composition/world
file that references `wolf_den_near_forest` (`grep -rl "wolf_den_near_forest"
data/worlds/*/world.yaml data/content/world_compositions/*.yaml`, 9 files):

- **`bandit_road_trade_pressure`'s `bandit_road` region** (`data/content/world_modules/bandit_road_trade_pressure.yaml:11`,
  `grid_bounds: [40,40,100,60]` → x:[40,100], y:[40,60], `terrain: "road"`) overlaps `near_forest`
  (x:[45,90], y:[40,55] — 46×16 = **736 tiles**) and `wolf_den` (x:[70,100], y:[40,60] — 31×21 =
  **651 tiles**). Arithmetic independently re-verified.
- **`goblin_camp_conflict`'s `goblin_camp` region** (`data/content/world_modules/goblin_camp_conflict.yaml:11`,
  `grid_bounds: [95,20,125,55]` → x:[95,125], y:[20,55]) overlaps `wolf_den` (x:[95,105], y:[30,55]
  — 11×26 = **286 tiles**). Arithmetic independently re-verified.

**Which of the 9 real files combine `wolf_den_near_forest` with `bandit_road_trade_pressure` and/or
`goblin_camp_conflict`?** Checked all 9 directly (grep for both module ids in each file):
| File | Combo present? |
|---|---|
| `data/content/world_compositions/frontier_marches` (via `data/worlds/frontier_marches/world.yaml`) | Both — confirmed by Review's own live compile |
| `data/content/world_compositions/frontier_extended.yaml` | Both |
| `data/content/world_compositions/frontier_living_world.yaml` | Both |
| `data/worlds/lifecycle_full_coverage_world/world.yaml` | `goblin_camp_conflict` only |
| `data/worlds/simq_scale_stress_seed42/world.yaml` | Both |
| `data/content/world_compositions/swamp_border_world.yaml` | Neither |
| `data/content/world_compositions/wilderness_survival.yaml` | Neither (confirmed separately, see Decision 3's original `survivor_camp_shelter` check, corrected in the Anti-Drift Hazards note below) |
| `data/worlds/sandbox_world/world.yaml` | Neither |
| `data/worlds/unit_faction_tension/world.yaml` | Neither (explicitly documented in its own file as reusing sandbox_world's exact `frontier_village_core` + `wolf_den_near_forest` pair only) |

**5 real, currently-shipping world compositions are affected**: `frontier_marches`, `frontier_extended`,
`frontier_living_world`, `lifecycle_full_coverage_world`, `simq_scale_stress_seed42`. The overlap box
*sizes* (736/651/286 tiles) are fixed by region bounds alone (seed-independent) and identical across
every affected composition — only the specific per-tile terrain *values* vary by each composition's own
seed, since the mechanism is the same deterministic `weighted_choice` draw regardless of which world it
runs in.

**Concrete measured example** (Review's own live compile of `data/worlds/frontier_marches/world.yaml`,
seed 603, plan's exact proposed YAML diff applied): `near_forest`×`bandit_road` → 547 forest / 189 swamp;
`wolf_den`×`bandit_road` → 495 forest / 156 swamp; `wolf_den`×`goblin_camp` → 220 forest / 66 swamp —
all within a few points of the target ~75%/25% ratio.

**Why this is pre-existing, not newly introduced**: `wolf_den_near_forest` is confirmed (both by Review's
live compile and by independent confirmation here that `bandit_road_trade_pressure`/`goblin_camp_conflict`
tie with `wolf_den_near_forest` at `requires: ["frontier_village_core"]` and lose the alphabetical
tie-break in `topological_sort_modules()`, `src/worldmodules/utils.py:7-44`) to already process **last**
in every one of these 5 compositions today — meaning these exact tile boxes are **already** silently
overwritten with flat `"forest"` pre-migration. This ticket does not create the overlap or change which
region wins it; it only changes what a tile-in-the-overlap-box's terrain *looks like* once it's won
(uniform forest → forest-dominant-with-swamp-patches).

**Decision: accept and explicitly document, do not attempt to fix.** Reasoning, extending Decision 3's
own logic to the cross-module case:
1. **No new correctness risk introduced.** `swamp` is confirmed legality-inert (no blocking/cover/high-ground
   in `legality.py`) — a `bandit_road` or `goblin_camp` tile turning to swamp cannot strand an entity or
   change tactical legality, exactly as already established for the intra-module case.
2. **The actual enforcement mechanism for "should regions be allowed to overlap at all" is a separate,
   pre-existing, unenforced Mechanics Bible law** (`allow_overlapping_regions`, confirmed unenforced by
   any code, see Current Behavior above) that predates this ticket and applies identically to every
   overlapping-region pair in the entire content corpus, not just `wolf_den_near_forest`'s. Fixing that
   enforcement gap is real, valuable follow-up work — but it is a validator/schema-level change spanning
   the whole corpus, explicitly out of this content-only ticket's blast radius (confirmed already in
   Decision 3's own follow-up flag).
3. **Reordering modules or regions to avoid the cross-module overlap is not a viable alternative**:
   module processing order is fully determined by `topological_sort_modules()`'s `requires`-edge +
   alphabetical-tie-break algorithm, not by any per-region declaration this ticket controls; changing it
   would require either adding a `requires` edge between unrelated ecology/conflict modules (semantically
   false — `wolf_den_near_forest` doesn't actually depend on `bandit_road_trade_pressure`) or renaming a
   module id purely to win an alphabetical sort, both of which are worse hacks than accepting the
   status quo.
4. **This is exactly the "make paint-order deliberate, not incidental" outcome the ticket asks for**,
   just extended one level beyond the intra-module case Decision 3 already covered — the fix is
   documentation (this section, plus an expanded YAML comment — see Docs Requiring Update below), not
   code or content restructuring.

**Not a blocking open question, but flagged for follow-up**: the Mechanics Bible's separate "Overlap
Policy" law (§2, `allow_overlapping_regions`) is confirmed unenforced by any code today (see Current
Behavior) — a pre-existing gap this ticket's migration does not create, worsen, or need to fix, but
whose existence is the reason `wolf_den_near_forest.yaml`'s overlap has never before been flagged as
a problem. Worth a future ticket (implement real overlap validation, or formally retire the
"Overlap Policy" law text if overlap is meant to always be tolerated) — **out of this ticket's scope,
does not block Plan**.

## Anti-Drift Hazards
- **Do not change `hazard_level`, `hazard_kind`, `tags`, `type`, or the existing `terrain` (flat)
  value for either region** — `test_hazard_kind_survives_module_pipeline` asserts `hazard_kind`
  exactly; the flat `terrain` value remains the noise-fill's own fallback/dominant weight and other
  tests assume both regions continue to resolve as `"wilderness"`-type with these hazard values.
- **Do not touch `WorldCompiler.compile()`, the schema files, or the resolver** — this ticket is
  YAML-content-only; the mechanism is already fully implemented and verified by tickets #1/#2. Adding
  even a no-op-looking code change here is scope creep into already-closed tickets' territory.
- **Do not reorder `near_forest`/`wolf_den` in the YAML `regions:` list** — Decision 3 above
  recommends keeping the current order (near_forest first, wolf_den second) as the deliberate choice;
  reordering would flip which region's terrain wins the overlap box and contradicts the documented
  rationale (wolf_den's higher hazard/namesake status should win).
- **Do not choose a legality-loaded secondary terrain** (`WALL`, `MOUNTAIN`, `HILL`, or `FOREST`
  used in a context where its cover semantics would matter) — `swamp` was specifically chosen partly
  *because* it is legality-inert, per Decision 2. Do not substitute a different secondary value in
  Plan/Implementation without re-checking `legality.py` for that value's semantics first.
  
- **Do not attempt to fix the `Overlap Policy` enforcement gap or the `TERRAIN_COST` casing bug** as
  part of this ticket — both are confirmed real, both are explicitly out of scope (the latter by the
  ticket's own text, the former by this investigation's own scoping judgment above); fixing either
  would balloon this ticket's blast radius far beyond one content file.
- **Do not rely on `state_hash`/certification-corpus equality as proof of correct per-tile terrain
  content** — `TCK-20260821-COMPILER-NOISE-FILL`'s investigation already established
  `StateFingerprinter`/`CanonicalStateHasher` both structurally exclude `state.terrain`. AC #2/#3's
  verification must inspect `state.terrain` dict content directly (see test_plan.md), exactly as that
  prior ticket's own test plan did.
- **Do not add a `terrain_variants` declaration to `frontier_village_core.yaml` or any other module**
  — Scope names only `wolf_den_near_forest.yaml`; `frontier_village_core.yaml` is read-only reference
  context in this ticket.
