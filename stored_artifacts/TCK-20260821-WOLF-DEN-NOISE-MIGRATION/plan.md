---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-WOLF-DEN-NOISE-MIGRATION
artifact_type: plan
tags: [world, content, determinism]
---

# Implementation Plan — TCK-20260821-WOLF-DEN-NOISE-MIGRATION

## Summary
Migrate `wolf_den_near_forest.yaml`'s two regions (`near_forest`, `wolf_den`) onto the already-live
`terrain_variants` noise-fill mechanism (`src/worldbuilding/compiler.py:211-236`, confirmed live by
investigation.md — no compiler/schema/resolver code changes needed) using a `forest`/`swamp`
weighted mix (3.0/1.0, ~75%/25%), keep the current YAML region order (`near_forest` first, `wolf_den`
second) as the deliberate, now-documented overlap-resolution rule for the shared
`x:[70,90],y:[30,55]` box, add a YAML comment recording that choice, add five new tests proving the
migration (field preservation, per-tile variation, overlap-winner identity, bit-identical
recompilation, and a fast field-preservation guard), update the Mechanics Bible's Noise-Fill Terrain
Law with a paint-order-for-overlaps bullet, and add one new parity ledger entry for this first
real-content usage. This is a content-and-docs-only change; `Do NOT touch` boundaries from
investigation.md are carried forward verbatim in Scope Guards below.

## Steps

### Step 1 — Edit `data/content/world_modules/wolf_den_near_forest.yaml`
**Files:** `data/content/world_modules/wolf_den_near_forest.yaml`

**Change:**
Add an identical `terrain_variants` list to both regions (confirmed schema shape at
`src/worldbuilding/schema.py:27-31`, `TerrainVariantSpec(terrain: str, weight: float = 1.0, gt=0.0)`,
`extra="forbid"`; confirmed field name/type on `RegionRecipeSpec` at `src/worldbuilding/recipe.py:20`):

```yaml
regions:
  # Overlap-resolution rule (deliberate, not incidental): wolf_den is declared after
  # near_forest, so per WorldCompiler.compile()'s declaration-order paint rule
  # (src/worldbuilding/compiler.py:211-236 — plain dict-key overwrite, last region in
  # spec.regions wins, no merge/blend), wolf_den's terrain (flat or noise-sampled) wins
  # every tile in the two regions' shared box x:[70,90], y:[30,55]. This is intentional:
  # wolf_den has the higher hazard_level (2.0 vs 1.0) and is the module's namesake
  # region, so the overlap zone should read as "den territory," not merely "near the
  # forest." Do not reorder these two entries without re-reading Decision 3 in
  # staging_artifacts/TCK-20260821-WOLF-DEN-NOISE-MIGRATION/investigation.md (or its
  # stored_artifacts copy after this ticket closes) — reordering flips which region's
  # terrain wins the overlap and contradicts this rationale.
  #
  # Cross-module overlap (also deliberate, see Decision 3b in the same investigation.md):
  # in real compositions that also include bandit_road_trade_pressure and/or
  # goblin_camp_conflict (frontier_marches, frontier_extended, frontier_living_world,
  # lifecycle_full_coverage_world, simq_scale_stress_seed42), near_forest/wolf_den
  # process last (topological_sort_modules()'s alphabetical tie-break), so tiles in
  # bandit_road's and goblin_camp's own bounds that fall inside near_forest/wolf_den's
  # bounds get forest/swamp noise-fill instead of their own module's flat terrain. This
  # pre-dates this migration (those tiles were already silently overwritten with flat
  # "forest"); swamp is legality-inert (no blocking/cover/high-ground), so this is a
  # cosmetic, accepted consequence, not a correctness risk.
  - id: "near_forest"
    type: "wilderness"
    grid_bounds: [45, 10, 90, 55]
    terrain: "forest"
    terrain_variants:
      - terrain: "forest"
        weight: 3.0
      - terrain: "swamp"
        weight: 1.0
    hazard_level: 1.0
    hazard_kind: "NATURAL_TERRAIN"
    tags: [forest]
  - id: "wolf_den"
    type: "wilderness"
    grid_bounds: [70, 30, 105, 70]
    terrain: "forest"
    terrain_variants:
      - terrain: "forest"
        weight: 3.0
      - terrain: "swamp"
        weight: 1.0
    hazard_level: 2.0
    hazard_kind: "NATURAL_TERRAIN"
    tags: [forest]
```

Weight ratio is fixed at `forest: 3.0, swamp: 1.0` (~75%/25%) per investigation.md's Decision 2
recommendation — forest-dominant so the module keeps its recognizable character while noise-fill
visibly diversifies terrain. **Do not give the two regions different weights.** The two regions can
safely reuse the identical `terrain_variants` list/weights (as done above) because
`WorldCompiler.compile()` (`src/worldbuilding/compiler.py:216-219`) derives each region's
`region_hash` from `r_spec.id` (`"near_forest"` vs `"wolf_den"` hash to different `region_hash`
values via the `(region_hash * 31 + ord(ch)) & 0xFFFFFFFF` fold), and folds that into a per-tile
`entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF` (line 224-225) before calling
`rng.weighted_choice(...)` — so even with byte-identical variant lists, `near_forest`'s hypothetical
draw and `wolf_den`'s actual draw for the *same* `(x,y)` tile use different RNG seeds and are not
required to agree. Step 2's Test #3 below proves `wolf_den` is the actual last writer by
recomputing its exact expected draw from its own `region_hash`, not by relying on the weights being
different (see Test #3 rationale — distinguishable weights alone would not prove *which* region's
draw won a given tile, since both regions draw from the same `{"forest","swamp"}` outcome space
either way).

**Only these two additions** (the `terrain_variants` block on each region, and the YAML comment
above the `regions:` list) are made. `id`, `type`, `grid_bounds`, `terrain` (flat/primary),
`hazard_level`, `hazard_kind`, `tags` are copied through unchanged on both regions, exactly as they
read today (confirmed exact current content by direct read, investigation.md lines 40-47 /
this session's own read of the file). The region list order (`near_forest` then `wolf_den`) is not
changed. Nothing outside the `regions:` block (`factions`, `populations`, `relationships`,
`resources`, `observability_tags`, `quest_definitions`, `requires`) is touched.

**Do NOT touch:** `type`, `hazard_level`, `hazard_kind`, `tags`, the flat `terrain` field, `id`,
`grid_bounds`, region list order, or any section of the file outside the two regions' new
`terrain_variants` blocks and the new comment.

**Verify:** New Test #1 (`test_wolf_den_near_forest_declares_terrain_variants`) and Test #5
(`test_wolf_den_near_forest_module_regions_preserve_non_terrain_fields`) from Step 2. Also: existing
`test_hazard_kind_survives_module_pipeline` and the four other `MODULE_MATRIX`-iterating tests in
`tests/integration/worldassembly/test_real_content_world_modules.py` must keep passing unmodified
(AC #4).

---

### Step 2 — Add the 5 new tests from test_plan.md
**Files:**
- `tests/integration/worldassembly/test_real_content_world_modules.py` (Tests #1 and #5 — append near
  the existing `test_hazard_kind_survives_module_pipeline` / `test_terrain_variants_survive_module_pipeline`
  functions, using the same `repos` fixture already defined in that file at lines 37-45)
- New file `tests/integration/worldassembly/test_wolf_den_noise_migration.py` (Tests #2, #3, #4)

**Change — file-placement decision (resolves test_plan.md's flagged open question for Test #2/#3/#4):**
Tests #2/#3/#4 require a full resolve→compile pipeline (`WorldAssemblyResolver.assemble()` +
`WorldCompiler.compile()`), which no test in `test_real_content_world_modules.py` currently performs
(that file's tests stop at `resolve_module_contribution()`, confirmed by direct read of every test in
that file above). A real, already-existing precedent for the exact resolve→compile pattern needed
exists at `tests/integration/worldassembly/test_real_content_world_compositions.py:333-371`
(`test_wilderness_survival_composition`) — it loads a real `WorldCompositionSpec` YAML, calls
`WorldAssemblyResolver(cat, mod).assemble(spec)` to get a `bundle` with `bundle.world_spec` and
`bundle.compile_context`, then calls
`WorldCompiler.compile(bundle.world_spec, seed=spec.generation_seed, context=bundle.compile_context)`.
That precedent test already compiles `wolf_den_near_forest` (via `wilderness_survival.yaml`) but
never inspects `state.terrain` per-tile content, so it cannot be reused as-is.

**Decision: do not reuse `wilderness_survival.yaml`.** Confirmed by direct read of every module it
composes (`forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield`,
`survivor_camp_shelter`): `survivor_camp_shelter`'s `survivor_outpost` region has
`grid_bounds: [30, 30, 60, 60]` → x:[30,60], y:[30,60], which overlaps `near_forest`'s bounds
(x:[45,90], y:[10,55]) in a third box, x:[45,60], y:[30,55].

**Corrected during Review**: this plan's first-pass reasoning incorrectly cited `ModuleRefSpec.order`
(declaration order in `module_refs`) as the tie-breaker, claiming `survivor_camp_shelter` (order 3)
would be the last writer over `wolf_den_near_forest` (order 1). This is backwards — `.order` only
drives an initial pre-sort (`src/worldassembly/resolver.py:277`) that is fully superseded by
`topological_sort_modules()` (`src/worldmodules/utils.py:7-44`), which ignores `.order` entirely and
sorts by `requires`-edges plus alphabetical tie-break. None of `wilderness_survival.yaml`'s 4 modules
`requires` any of the others present in this composition (`frontier_village_core` isn't included, and
none of the 4 requires another of the 4), so all 4 tie at in-degree 0 and sort alphabetically:
`forest_deep_ecology, survivor_camp_shelter, undead_battlefield, wolf_den_near_forest` — meaning
`wolf_den_near_forest` (hence `near_forest`) is processed **last**, not `survivor_camp_shelter` as
originally (incorrectly) stated. The practical conclusion is unaffected — a minimal, dedicated
synthetic composition is still the right call for Tests #2-4, and is in fact *more* defensible now:
it deliberately avoids reasoning about this whole class of cross-module overlap (see the newly-added
Decision 3b in investigation.md, which found and explicitly resolved this same overlap class for two
*other* real modules — `bandit_road_trade_pressure`, `goblin_camp_conflict` — across 5 real,
currently-shipping compositions) rather than accidentally sidestepping it via a since-corrected wrong
reason.

**Instead, build a minimal synthetic composition** in Python, mirroring the `_make_comp` helper
pattern already used at `tests/integration/content/test_swamp_border_pack.py:133-140` (which builds
a `WorldCompositionSpec.model_validate({...,"modules": module_ids})` using the shorthand `modules`
field — confirmed present on `WorldCompositionSpec` at `src/worldassembly/schema.py:33`,
`modules: Optional[List[str]] = Field(None, ...)`):

```python
def _make_comp():
    from src.worldassembly.schema import WorldCompositionSpec
    return WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": "wolf_den_noise_migration_test",
        "name": "Wolf Den Noise Migration Test",
        "modules": ["frontier_village_core", "wolf_den_near_forest"],
        "generation_seed": 4242,
    })
```

No `global_parameters.topology_width/height` is set deliberately: confirmed by direct read of
`src/worldassembly/resolver.py:654-662`, when not explicitly given, width/height are auto-computed as
`max(100, max region max_x + 1)` / `max(100, max region max_y + 1)` across every resolved region —
since `wolf_den`'s bounds reach x_max=105, y_max=70, this auto-computes width=106, height=100,
comfortably covering both regions without the implementer needing to hardcode a topology size
(satisfies test_plan.md Test #2's "topology large enough to contain both regions' bounds, e.g.
width/height ≥ 106" requirement automatically). `frontier_village_core`'s `hometown` region
(`grid_bounds: [10,10,40,40]` → x:[10,40], y:[10,40], confirmed by direct read) does not overlap
either wolf-den region (5-tile gap, confirmed by investigation.md) — it is included specifically to
give Test #2 a real, in-composition "outside both regions" comparison point (`terrain=="plain"`),
matching test_plan.md's suggested check, in addition to the base-fill check at `(0,0)`.

Resolve pipeline for all three tests in the new file, via a module-scoped fixture:
```python
@pytest.fixture(scope="module")
def compiled_state():
    cat = CatalogRepository("data/content"); cat.load_all()
    mod = WorldModuleRepository(); mod.load_all()
    spec = _make_comp()
    bundle = WorldAssemblyResolver(cat, mod).assemble(spec)
    state, report = WorldCompiler.compile(
        bundle.world_spec, seed=spec.generation_seed, context=bundle.compile_context
    )
    return state
```

**Test #2 — `test_wolf_den_near_forest_compiles_with_per_tile_terrain_variation`** (new file):
- Base-fill check: `state.terrain[(0, 0)] == "PLAIN"` (confirmed base-fill value at
  `src/worldbuilding/compiler.py:203-205` — every tile is initialized to the literal string
  `"PLAIN"` before any region is painted).
- Outside-both-regions check: every tile in `frontier_village_core`'s `hometown` bounds
  (x:[10,40], y:[10,40]) equals `"plain"` (the module's own flat `terrain` value, confirmed at
  `data/content/world_modules/frontier_village_core.yaml`, read directly — `terrain: "plain"`,
  `hometown` has no `terrain_variants`, so it keeps the flat fill per
  `docs/mechanics/06_worldbuilding_foundation.md`'s existing "Non-Declaring Regions" bullet).
- `near_forest`-own-variation check: iterate tiles in `near_forest`'s bounds
  (x:[45,90], y:[10,55]) **excluding** the `wolf_den` overlap box (x:[70,90], y:[30,55]) — i.e. only
  tiles where `x < 70 or y < 30 or y > 55` (all such tiles are outside `wolf_den`'s bounds too, since
  `wolf_den` is x:[70,105], y:[30,70] — confirmed no other module region in this 2-module composition
  reaches into this sub-area) — assert at least one such tile's terrain differs from `"forest"`.
  With 1570 such tiles at a fixed 25% swamp draw probability each, `P(all "forest")` is
  astronomically small; not a flake risk.
- `wolf_den`-variation check: iterate all tiles in `wolf_den`'s bounds (x:[70,105], y:[30,70]) —
  1476 tiles — assert at least one differs from `"forest"`. (`wolf_den` is always the last writer for
  every tile in its own bounds in this 2-module composition, so no exclusion is needed here.)

**Test #3 — `test_wolf_den_overlap_box_resolves_to_wolf_den_terrain`** (new file):
Directly proves Decision 3 ("wolf_den wins the overlap") using investigation.md's recommended
Option 2 (exact recomputation), not distinguishable weights — see Step 1's rationale for why
distinguishable weights alone would not prove *which* region won a given tile. For every tile
`(x, y)` in the overlap box `x:[70,90], y:[30,55]` (546 tiles), recompute the exact expected draw
using `wolf_den`'s own `region_hash`/`entity_id` formula, byte-for-byte matching
`src/worldbuilding/compiler.py:216-231`:
```python
from src.platform.rng import DeterministicRNG
from src.core.enums import Domain

def _expected_wolf_den_terrain(rng, x, y):
    region_hash = 0
    for ch in "wolf_den":
        region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF
    tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)
    entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF
    return rng.weighted_choice(
        Domain.INIT, tick=0, entity_id=entity_id,
        seq=["forest", "swamp"], weights=[3.0, 1.0], sub_id=1,
    )

def test_wolf_den_overlap_box_resolves_to_wolf_den_terrain(compiled_state):
    state = compiled_state
    rng = DeterministicRNG(4242)  # must match _make_comp()'s generation_seed
    for x in range(70, 91):
        for y in range(30, 56):
            assert state.terrain[(x, y)] == _expected_wolf_den_terrain(rng, x, y)
```
`DeterministicRNG` is confirmed stateless/pure per `(base_seed, domain, tick, entity_id, sub_id)`
(`src/platform/rng.py:100-103`, `_composite_seed` has no counter/mutation), so a freshly constructed
`DeterministicRNG(4242)` outside `compile()` reproduces byte-identical draws to the one `compile()`
used internally — this is the same technique
`tests/unit/worldbuilding/test_world_compiler.py`'s existing `terrain_variants` unit tests already
rely on (compiler-mechanism regression surface named in test_plan.md's Unit section).
Import `Domain` from `src.core.enums` (confirmed `class Domain(IntEnum)` at `src/core/enums.py:168`,
with `INIT` a member — confirmed used by `compiler.py:227` as `Domain.INIT`), not from
`src.platform.rng` (that module only defines `DeterministicRNG` itself).

**Test #4 — `test_wolf_den_near_forest_recompile_same_seed_is_bit_identical`** (new file):
Compile `_make_comp()` twice with the same seed (4242) via a second call to
`WorldAssemblyResolver(...).assemble(...)` + `WorldCompiler.compile(...)` (do not reuse the module-
scoped `compiled_state` fixture for both sides — call the pipeline directly twice inside this one
test so both compiles are independent). Assert full `state.terrain == state.terrain` dict equality
(not just `state_hash` — per investigation.md and `TCK-20260821-COMPILER-NOISE-FILL`'s own
investigation, `StateFingerprinter`/`CanonicalStateHasher` structurally exclude `state.terrain`, so
hash equality alone proves nothing about terrain content) and `report["state_hash"] ==
report["state_hash"]` (belt-and-suspenders, supplementary only). Then compile a third time with a
different seed (e.g. 9999) and assert `state.terrain` restricted to the union of `near_forest` and
`wolf_den` bounds differs from the seed-4242 result (sanity check that noise-fill is actually
seed-sensitive for this real content).

**Test #1 — `test_wolf_den_near_forest_declares_terrain_variants`** (existing file, uses the `repos`
fixture already at `test_real_content_world_modules.py:37-45`): load `wolf_den_near_forest` via
`mod.get_module(...)`, assert both regions' `terrain_variants` is a non-empty list, assert both
regions' flat `terrain` field is still exactly `"forest"`, and assert `hazard_level`/`hazard_kind`/
`tags`/`type` are unchanged (`1.0`/`2.0`, `"NATURAL_TERRAIN"`, `["forest"]`, `"wilderness"`) —
mirrors the existing `test_hazard_kind_survives_module_pipeline`/`test_terrain_variants_survive_module_pipeline`
pattern (same file, lines 113-191, already read in full).

**Test #5 — `test_wolf_den_near_forest_module_regions_preserve_non_terrain_fields`** (existing file,
same fixture): narrower, faster duplicate of part of Test #1's field-preservation assertions on the
*resolved* contribution (post `resolve_module_contribution()`), kept separate per test_plan.md so a
future terrain-only regression and a future field-drift regression fail independently rather than
under one assertion block.

**Do NOT touch:** any existing test function body in `test_real_content_world_modules.py`
(`test_hazard_kind_survives_module_pipeline` in particular — test_plan.md's Anti-Drift Test Guards
explicitly forbid editing it), `MODULE_MATRIX`, the `repos` fixture, or any file in
`test_real_content_world_compositions.py` / `test_swamp_border_pack.py` (read-only precedent
references only).

**Verify:**
```
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/integration/worldassembly/test_wolf_den_noise_migration.py \
       tests/integration/content/test_strict_world_matrix.py \
       tests/integration/content/test_resource_region_coverage_corpus.py \
       tests/integration/content/test_swamp_border_pack.py \
       tests/unit/worldbuilding/ \
       tests/certification/test_world_compile_determinism.py \
       -v -m "not slow"
```
(test_plan.md's scoped command, plus the new file added explicitly since it did not exist when
test_plan.md was written.)

---

### Step 3 — Update `docs/mechanics/06_worldbuilding_foundation.md`
**Files:** `docs/mechanics/06_worldbuilding_foundation.md`

**Change:** Add one new bullet to the existing `### Noise-Fill Terrain Law` subsection (confirmed
current content at lines 34-39, read in full above), immediately after the existing "Non-Declaring
Regions" bullet and before "Bounds Clamp Unchanged", stating the compiler's actual, confirmed-by-code
overlap behavior generically (not naming `wolf_den_near_forest`, per investigation.md's Docs
Requiring Update instruction):

```markdown
*   **Paint Order for Overlapping Regions**: `WorldSpec.regions` is iterated in declaration order,
    and each region's terrain write (flat or noise-sampled) is a plain dict-key overwrite —
    `WorldCompiler.compile()` performs no merge or blend. For any tile that falls inside more than
    one region's bounds, the region later in declaration order overwrites the terrain of any region
    processed earlier for that tile, unconditionally. Content authors intending an overlap must treat
    declaration order as the deliberate priority mechanism and document that intent in the module's
    own YAML (there is no separate schema-level priority field).
```

Only this one bullet is added. Do not edit any other bullet in this subsection, and do not touch
`### Spatial Laws` (the "Overlap Policy" text one section up) — investigation.md confirms that
policy's enforcement gap is a separate, pre-existing, out-of-scope issue this bullet does not resolve
or reference.

**Do NOT touch:** the frontmatter, any other chapter section, `## 3. Entity & Resource Distribution`,
or `docs/core/state.md`.

**Verify:** `tests/docs/test_doc_integrity.py` (doc-structure/frontmatter sanity — not in the
test_plan.md scoped command since it's a generic doc-integrity check, not subsystem-specific; run
manually as a lightweight sanity pass, not blocking on the scoped pytest command above).

---

### Step 4 — Add a new parity ledger entry
**Files:** `docs/parity_ledger/substrate.yaml`, via `tools/parity_ledger_writer.write_entry()` only —
no direct YAML file edit.

**Change:** `SUB-385` (`docs/parity_ledger/substrate.yaml:4806-4826`, confirmed `status: verified`,
`priority: P2`, already describing the schema+compiler mechanism generically with
`test_path: tests/unit/worldbuilding/test_world_compiler.py::test_compiler_terrain_variants_deterministic_same_seed`)
is **not** mutated. Add a new, distinct entry documenting that `wolf_den_near_forest.yaml` is the
first real content module to declare `terrain_variants` in production. Confirmed the next available
id by grepping every `- id: SUB-3XX` line in `docs/parity_ledger/substrate.yaml` at investigation/plan
time: the highest existing id is `SUB-385` (line 4806) — **`SUB-386` is next available as of this
plan**, but per this batch's established convention (and this file's own multi-writer nature — see
below), the implementer must re-run `grep -n "^- id: SUB-3" docs/parity_ledger/substrate.yaml | tail -5`
immediately before writing, in case a sibling ticket in this same batch or another concurrent session
has claimed `SUB-386` since this plan was written, and use the next free id if so.

**Other writers to this shared resource:** `docs/parity_ledger/substrate.yaml` is a single shard file
appended to by every ticket in this table's subsystem — confirmed no other ticket in this 5-ticket
batch is still in-flight as of this plan (this is the batch's final ticket), but `write_entry()`
(`tools/parity_ledger_writer.py:88-117`) itself is safe against the general concurrent-write case: it
reads the full shard, upserts by `id` (replacing an existing entry with the same id or appending a
new one), and rewrites the whole file, then rebuilds the derived index — it is not an atomic
multi-writer-safe operation at the filesystem level (a second process's stale read-then-write could
clobber this entry if run truly simultaneously), which is exactly why the implementer must call
`write_entry()` itself (not hand-edit the YAML) and must re-grep for the next-free id immediately
before calling it rather than trusting this plan's `SUB-386` number, per this repo's own established
convention for this ledger file.

Entry fields (per `validate_entry()`, `tools/parity_ledger_writer.py:64-85`: `status: "verified"`
independently requires non-empty `v2_evidence` and `test_path` regardless of priority — this is not
a `P0`-specific rule; the separate `priority == "P0"` branch at lines 82-85 is an *additional*,
independent gate that would apply on top if this entry were P0. This plan's `test_path` below is
therefore required, not merely supplied "per repo convention" as an earlier draft of this plan
imprecisely stated — corrected during Review):
```python
write_entry("substrate.yaml", {
    "id": "SUB-386",  # re-grep and confirm free at implementation time, see above
    "text": (
        "wolf_den_near_forest.yaml's near_forest and wolf_den regions (data/content/"
        "world_modules/wolf_den_near_forest.yaml) are the first real content module regions "
        "to declare terrain_variants in production (forest weight=3.0, swamp weight=1.0, "
        "~75%/25%), exercising the SUB-385 compiler mechanism for the first time with real "
        "content instead of synthetic test fixtures. The two regions' bounds genuinely "
        "overlap in x:[70,90],y:[30,55]; wolf_den is declared second in the module's "
        "regions: list, so per WorldCompiler.compile()'s declaration-order paint rule its "
        "terrain (flat or noise-sampled) wins every tile in the shared box, documented "
        "explicitly via a YAML comment above the regions: list and via the Mechanics "
        "Bible's Noise-Fill Terrain Law 'Paint Order for Overlapping Regions' bullet."
    ),
    "status": "verified",
    "priority": "P2",
    "legacy_evidence": None,
    "v2_evidence": "data/content/world_modules/wolf_den_near_forest.yaml (terrain_variants on "
                   "both near_forest and wolf_den regions)",
    "proof_type": None,
    "test_path": "tests/integration/worldassembly/test_wolf_den_noise_migration.py::"
                 "test_wolf_den_overlap_box_resolves_to_wolf_den_terrain",
    "divergence_note": None,
})
```

**Do NOT touch:** `SUB-385` itself (any field), any other entry in `substrate.yaml`, or any other
parity ledger shard file. Do not hand-edit the YAML file directly — use `write_entry()` only, so the
derived index rebuild (`build()`, called internally by `write_entry()`) stays consistent.

**Verify:** `tools/parity_ledger_writer.py`'s own `build()` call inside `write_entry()` succeeding
(returns `{"status": "ok", ...}`, raises `EntryValidationError` otherwise) is the direct verification;
additionally confirm `docs/parity_ledger/substrate.yaml` still parses as valid YAML with `SUB-385`
byte-unchanged after the write.

## Scope Guards
Verbatim from investigation.md's Anti-Drift Hazards:
- Do not change `hazard_level`, `hazard_kind`, `tags`, `type`, or the existing `terrain` (flat) value
  for either region — `test_hazard_kind_survives_module_pipeline` asserts `hazard_kind` exactly; the
  flat `terrain` value remains the noise-fill's own fallback/dominant weight and other tests assume
  both regions continue to resolve as `"wilderness"`-type with these hazard values.
- Do not touch `WorldCompiler.compile()`, the schema files, or the resolver — this ticket is
  YAML-content-only; the mechanism is already fully implemented and verified by tickets #1/#2. Adding
  even a no-op-looking code change here is scope creep into already-closed tickets' territory.
- Do not reorder `near_forest`/`wolf_den` in the YAML `regions:` list — Decision 3 recommends keeping
  the current order (near_forest first, wolf_den second) as the deliberate choice; reordering would
  flip which region's terrain wins the overlap box and contradicts the documented rationale (wolf_den's
  higher hazard/namesake status should win).
- Do not choose a legality-loaded secondary terrain (`WALL`, `MOUNTAIN`, `HILL`, or `FOREST` used in a
  context where its cover semantics would matter) — `swamp` was specifically chosen partly because it
  is legality-inert, per Decision 2. Do not substitute a different secondary value without re-checking
  `legality.py` for that value's semantics first.
- Do not attempt to fix the `Overlap Policy` enforcement gap or the `TERRAIN_COST` casing bug as part
  of this ticket — both are confirmed real, both are explicitly out of scope; fixing either would
  balloon this ticket's blast radius far beyond one content file.
- Do not rely on `state_hash`/certification-corpus equality as proof of correct per-tile terrain
  content — `StateFingerprinter`/`CanonicalStateHasher` both structurally exclude `state.terrain`.
  AC #2/#3's verification must inspect `state.terrain` dict content directly.
- Do not add a `terrain_variants` declaration to `frontier_village_core.yaml` or any other module —
  Scope names only `wolf_den_near_forest.yaml`; `frontier_village_core.yaml` is read-only reference
  context in this ticket.

## Dependency Map
All four steps are independent of each other (no step's file output is consumed as input by another
step's implementation — no shared code path is edited by more than one step). Suggested execution
order is Step 1 → Step 2 (tests need the migrated YAML to pass, though the test *files* can be written
before Step 1 lands) → Step 3 → Step 4, purely so each step can be verified in isolation as it lands,
matching this plan's step numbering. Step 2's tests will fail (not error) if run before Step 1 lands;
Step 3 and Step 4 have no code/test dependency on Steps 1-2 at all and could be done in any order
relative to them.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: both regions declare `terrain_variants` with an explicit, documented overlap-resolution choice (not incidental order) | Step 1 (YAML `terrain_variants` + comment), Step 3 (Mechanics Bible bullet) | Test #1 (`test_wolf_den_near_forest_declares_terrain_variants`), Test #5 (`test_wolf_den_near_forest_module_regions_preserve_non_terrain_fields`) |
| AC #2: fixed-seed compile produces at least one differing tile inside each region's bounds; tiles outside both regions unaffected | Step 1 (YAML), Step 2 (new test file) | Test #2 (`test_wolf_den_near_forest_compiles_with_per_tile_terrain_variation`) |
| AC #2 (overlap-specific): overlap box resolves to `wolf_den`'s terrain, not `near_forest`'s | Step 1 (order kept + comment), Step 2 | Test #3 (`test_wolf_den_overlap_box_resolves_to_wolf_den_terrain`) |
| AC #3: recompiling same world+seed twice is bit-identical (`state.terrain` and `state_hash`) | Step 1 (deterministic YAML content), Step 2 | Test #4 (`test_wolf_den_near_forest_recompile_same_seed_is_bit_identical`) |
| AC #4: existing `test_real_content_world_modules.py` pipeline tests keep passing unmodified | Step 1 (no field changes outside `terrain_variants`) | Full existing test suite in `test_real_content_world_modules.py`, run unmodified via the scoped pytest command |

## Anti-Drift Notes
- `DeterministicRNG` is a stateless composite-key hash (`src/platform/rng.py:100-103`) — authoring
  `terrain_variants` on these two regions cannot perturb any other region's or entity's *RNG draw
  values* regardless of value count/weights (no other region's `weighted_choice()` call receives a
  different key or produces a different result). **Correction from an earlier draft of this plan**:
  this does NOT mean no other module's *final compiled terrain content* changes — per investigation.md's
  Decision 3b (added during Review), `bandit_road_trade_pressure`'s and `goblin_camp_conflict`'s own
  region bounds genuinely overlap `near_forest`/`wolf_den` in 5 real, currently-shipping compositions,
  and since `near_forest`/`wolf_den` process last in all of them, tiles inside those overlap boxes now
  show forest/swamp noise-fill instead of `bandit_road`/`goblin_camp`'s own flat terrain — a real,
  measured, explicitly accepted (not overlooked) consequence, documented in the YAML comment above and
  in investigation.md's Decision 3b, not a new correctness risk (swamp is legality-inert).
- `state_hash`/`StateFingerprinter` structurally exclude `state.terrain` — never treat hash equality
  as sufficient proof of correct terrain content in any new or existing test; Test #4's hash check is
  supplementary only, its `state.terrain` dict-equality check is load-bearing.
- The `Overlap Policy` law in the Mechanics Bible (`allow_overlapping_regions`) is confirmed unenforced
  by any code today — this migration operates inside that pre-existing, unrelated gap and must not
  attempt to close it (e.g. do not set `allow_overlapping_regions: true` anywhere, do not add bounds
  validation). `tests/unit/worldbuilding/test_worldspec_schema.py:51`'s default-`False` assertion must
  stay accurate and untouched.
- `TERRAIN_COST`'s uppercase-vs-lowercase casing bug (`src/core/state.py:344-354`) means the new
  `"swamp"` secondary terrain has zero live movement-cost effect today, exactly like the existing
  `"forest"` value already does — no test in this plan asserts on `TERRAIN_COST`-derived movement cost.
- `test_hazard_kind_survives_module_pipeline` must not be edited under any circumstance while
  implementing this plan — if a change to it appears necessary, stop and treat that as a signal the
  migration broke `hazard_kind` preservation, not that the test needs updating.
- Test #3's overlap-box proof depends on `_make_comp()`'s `generation_seed` (4242) matching the seed
  passed to `DeterministicRNG(...)` in the recomputation helper — if the implementer changes the
  fixture's seed value for any reason, both call sites must be updated together or the test will fail
  for an unrelated reason (seed mismatch, not a real regression).

## Verification
Exact scoped pytest command from test_plan.md, extended with the new test file created in Step 2
(test_plan.md predates this file's creation and could not name it):
```
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/integration/worldassembly/test_wolf_den_noise_migration.py \
       tests/integration/content/test_strict_world_matrix.py \
       tests/integration/content/test_resource_region_coverage_corpus.py \
       tests/integration/content/test_swamp_border_pack.py \
       tests/unit/worldbuilding/ \
       tests/certification/test_world_compile_determinism.py \
       -v -m "not slow"
```
Never run the bare `pytest tests/`. Do not add or remove any test file from this scope without
updating this section.
