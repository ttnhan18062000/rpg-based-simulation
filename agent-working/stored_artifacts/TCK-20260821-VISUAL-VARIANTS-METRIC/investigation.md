---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-VARIANTS-METRIC
artifact_type: investigation
tags: [visualization, simulation-quality, determinism, world]
---

# Investigation — TCK-20260821-VISUAL-VARIANTS-METRIC

## Current Behavior

- `experiments/spatial_rendering/prototype/render_trail.py` (full file read): tracks exactly one
  entity across `total_ticks` (default 200), sampled every `sample_every` ticks (default 10). Entity
  selection is `tracked_id = next(iter(state.entities.keys()))` (line 35) — the hardcoded "first
  entity in dict" the ticket's Scope requires replacing. Per sample it reads
  `kernel._state.entities.get(tracked_id)`, checks `ent.lifecycle.active`, and records
  `(tick, int(x), int(y))` from `ent.navigation.position`. It never computes a trail-activity ratio
  today — it only renders a breadcrumb PNG. No `unique_tiles_visited / ticks_sampled` computation
  exists anywhere in the codebase yet (confirmed by grep — zero hits for "trail_activity" or
  "activity_ratio" outside `PROPOSAL.md`'s prose).
- `experiments/spatial_rendering/prototype/render_world.py::render()` (lines 90-95) builds
  `terrain_histogram: dict[str, int]` as a side effect of rendering, by counting raw (non-normalized)
  terrain-type strings.
- `src/rendering/density.py::compute_terrain_histogram(terrain: dict) -> dict[str, int]` (lines
  58-62) is a **verbatim extraction** of that exact counting logic (its own docstring says so, lines
  16-18) — same raw-count-per-type-string output, no normalization, no case-folding. It is a pure
  function over a plain `terrain` dict, no `AuthoritativeState` coupling.
- `total_variation_distance` does not exist anywhere in `src/` yet. `PROPOSAL.md:409-413` gives the
  only implementation, over already-**normalized** histograms (`dict[str, float]` summing to ~1.0):
  `0.5 * sum(abs(h1.get(k,0) - h2.get(k,0)) for k in set(h1)|set(h2))`.
- Siblings' pattern (`src/rendering/connectivity.py`, `src/rendering/shape.py`, both read in full):
  frozen `@dataclass` result types, pure functions over `terrain`/`blocked_tiles` dicts, no
  `AuthoritativeState` parameter — callers pass already-extracted primitives. Both modules' opening
  docstrings cite exactly which `PROPOSAL.md` line range they port and log a Ticket ID. Both are
  covered by `tests/architecture/test_rendering_zero_new_dependency_guard.py` (stdlib-only import
  guard, package-wide) plus (for `shape.py`/`density.py` only — **not** `connectivity.py`, a real gap
  in the sibling pattern, not something to copy) an in-file AST-walk test pair:
  `test_<module>_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` and
  `test_<module>_module_has_zero_image_or_render_dependency` (`tests/unit/rendering/test_density.py:130-166`,
  `tests/unit/rendering/test_shape.py:236-273`).

## THE CRITICAL FINDING — seed-variance is real, but does not currently reach either AC #2 anchor world through the normal load path

**Empirically verified by actually compiling, twice, at two different seeds, and diffing real terrain
dicts and histograms — not assumed.**

1. **`wolf_den_near_forest.yaml` is the only world module in the entire corpus with `terrain_variants`
   set** (`grep -rl terrain_variants data/content/world_modules/` — exactly one hit). `dungeon_crawl`'s
   four modules (`ruins_mystery_quest`, `goblin_camp_conflict`, `old_mine_resource_loop`,
   `scalable_bandit_camp`) were checked individually — **none** declare `terrain_variants`.
2. **9 real world compositions reference `wolf_den_near_forest`** (`grep -l wolf_den_near_forest
   data/worlds/*/world.yaml`): `sandbox_world`, `frontier_marches`, `frontier_extended`,
   `lifecycle_full_coverage_world`, `frontier_living_world`, `simq_scale_stress_seed42`,
   `swamp_border_world`, `unit_faction_tension`, `wilderness_survival`. **`sandbox_world` — one of
   AC #2's two anchor worlds — is one of the nine.**
3. **`WorldRepository.load_world()` (`src/worldbuilding/repository.py:63-87`) never re-resolves a
   composition world from source.** For any `schema_version` containing `"worldcomposition"` (both
   `sandbox_world` and `dungeon_crawl` qualify — `schema_version: "worldcomposition.v1"`, confirmed
   directly), it redirects straight to the **pre-existing, on-disk**
   `resolved/world.resolved.yaml` cache file (lines 77-80) and never touches the raw module YAML or
   `WorldAssemblyResolver` again.
4. **`data/worlds/sandbox_world/resolved/world.resolved.yaml` is stale relative to
   `wolf_den_near_forest.yaml`.** Confirmed directly: `grep -A15 wolf_den
   data/worlds/sandbox_world/resolved/world.resolved.yaml` shows the `wolf_den` region entry with
   `terrain: forest` (flat, single value) and **no `terrain_variants` key at all**. Cross-checked
   against `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s own "Files Changed" list (`tickets/done/
   TCK-20260821-WOLF-DEN-NOISE-MIGRATION.md`): it edited only the raw module YAML, two test files,
   one Mechanics Bible doc, and the parity ledger — it never ran `make world-resolve WORLD=<x>` for
   any of the 9 downstream compositions. **This is a real, live gap this ticket did not create and is
   not scoped to fix, but that materially changes what "the confirmed seed-invariant-terrain finding"
   currently means.**
5. **Empirical test 1 — using the real, on-disk load path exactly as any production caller (and this
   ticket's own code) would use it** (`WorldRepository("data/worlds").load_world(world_id)` →
   `WorldCompiler.compile(spec, seed=N)`, run twice per world at seed 42 and seed 137, terrain dicts
   diffed tile-by-tile): **`sandbox_world`'s terrain dict is byte-identical across both seeds — 0
   diffs out of 10,600 tiles.** `dungeon_crawl`'s terrain dict is likewise byte-identical across both
   seeds. **As things stand on disk today, AC #3 holds for both anchor worlds, but for `sandbox_world`
   this is an artifact of the stale resolved-cache redirect, not evidence the module's mechanism is
   inert.**
6. **Empirical test 2 — bypassing the stale cache**, replicating exactly what `src/worldbuilding/
   cli.py::handle_resolve()` does (load raw `world.yaml` → `WorldCompositionSpec.model_validate()` →
   `WorldAssemblyResolver(cat_repo, mod_repo).assemble(composition)` → `bundle.world_spec`), but
   **in-memory, without writing the refreshed `resolved/world.resolved.yaml` back to disk** (no
   durable state was mutated by this investigation): the freshly-resolved `sandbox_world` spec's
   `near_forest` and `wolf_den` regions **do** carry `terrain_variants=[forest(w=3.0),
   swamp(w=1.0)]` (confirmed via `src/worldassembly/resolver.py:800`, which passes
   `terrain_variants=getattr(reg, "terrain_variants", None)` through into the resolved `RegionSpec`).
   Compiling that freshly-resolved spec at seed 42 vs. seed 137 produces a **genuinely different**
   terrain histogram: `forest: 2292 (seed 42) vs. 2278 (seed 137)`, `swamp: 754 (seed 42) vs. 768
   (seed 137)` — a real, non-zero difference, exactly as the noise-fill mechanism's own design
   intends. `dungeon_crawl`, freshly resolved the same way, is still byte-identical across seeds
   (correctly — none of its modules declare `terrain_variants`).

**Conclusion, precise, not hedged:**
- **`dungeon_crawl` is robustly, structurally seed-invariant** — no module in its composition chain
  declares `terrain_variants` anywhere, so its terrain cannot vary by seed regardless of whether its
  resolved cache is ever refreshed. This is the correct, durable anchor for AC #3's "same-spec/
  different-seed TVD == 0.0" test.
- **`sandbox_world` is NOT a safe seed-invariance anchor**, even though it currently passes. Its
  seed-invariance today is entirely a side effect of a stale `resolved/world.resolved.yaml` that
  nobody has regenerated since `TCK-20260821-WOLF-DEN-NOISE-MIGRATION` landed. The moment anyone runs
  `make world-resolve WORLD=sandbox_world` (a normal, expected maintenance operation with its own
  Makefile target, `world-resolve`) — for any reason, entirely unrelated to this ticket — `sandbox_world`
  silently starts producing seed-varying terrain, and a test anchored to it would start failing with
  zero code change in this ticket's own module. **A test built on this ticket's own honest empirical
  work must not encode a claim ("sandbox_world's terrain is seed-invariant") that is already false
  one resolve-cache refresh away from being wrong.**
- **AC #2's cross-spec anchor (`TVD(sandbox_world, dungeon_crawl) ≈ 0.2315` at seed 42) is unaffected
  either way** — it only ever compares one fixed seed (42) per world, so cache staleness vs.
  freshness doesn't change which single terrain snapshot gets compared; verified directly (see next
  section).
- **AC #4 ("no code path treats same-spec/different-seed as a diversity signal") is now more
  important, not less**, given the finding: `total_variation_distance()` itself must stay a pure,
  spec-agnostic statistical function over two histograms with no awareness of "which world/seed pair
  produced them" — the *caller* (or a future orchestration layer, out of this ticket's scope per
  `Out of Scope`) is responsible for only ever feeding it cross-spec pairs. This module must not grow
  any internal same-spec-different-seed comparison logic, now or later, even for `sandbox_world`-style
  worlds where such a comparison would (as of any future resolve refresh) produce a non-zero, and
  therefore temptingly "interesting", result.

## TVD Formula — verified against the anchor by actually computing it

`PROPOSAL.md:409-413`: `total_variation_distance(h1: dict[str,float], h2: dict[str,float]) -> float
= 0.5 * sum(abs(h1.get(k,0) - h2.get(k,0)) for k in set(h1)|set(h2))`. This is the standard TVD over
two categorical distributions and requires **h1/h2 to already be normalized proportions** (values
summing to 1.0 each) — the formula's own shape (a `0.5 * Σ|Δ|` bounded to `[0,1]`) only holds for
proportions, not raw counts.

`compute_terrain_histogram()` (reused from `density.py`, see below) returns **raw counts**, not
proportions — `sandbox_world` has 10,600 total terrain tiles at seed 42, `dungeon_crawl` has a
different total. Feeding raw counts directly into the formula above would not reproduce the anchor
and would not be bounded `[0,1]`.

**Verified directly, reproducing the exact anchor:** normalizing each raw histogram to proportions
(`{k: v/sum(h.values()) for k, v in h.items()}`) first, then applying the formula above to
`sandbox_world` (seed 42) vs. `dungeon_crawl` (seed 42) via the real, on-disk load path, gives
**`0.23161981243456373`** — rounds to the documented `0.2315` anchor exactly. Confirmed this is not
sensitive to the stale-cache issue above: this comparison only ever needs one seed per world, and the
seed-42 terrain for both worlds is identical whether loaded via the stale cache or freshly resolved
(seed 42 was the seed both original resolved caches were generated from).

**Implementation implication:** the module needs a small `normalize_histogram(raw: dict[str, int]) ->
dict[str, float]` helper (division by `sum(raw.values())`, empty-input guarded) sitting between
`compute_terrain_histogram()`'s raw-count output and `total_variation_distance()`'s
already-normalized-input contract — `total_variation_distance` itself should stay exactly as
`PROPOSAL.md` specifies it (proportions in, float out), matching the ticket's own Assumptions note
that this formula is "written fresh from PROPOSAL.md §5c," not reinvented with built-in
normalization.

## Trail-Activity Formula — precise denominator, verified against the cited evidence

`PROPOSAL.md:141` and this ticket's AC #1 both cite the same real number: **"~2-3 tiles/100+ ticks"**
for the confirmed-stuck pattern, from a run that sampled every 10 ticks over 200 total ticks (20
actual position samples, `render_trail.py` defaults). Since the cited ratio is stated per **total
ticks run** (100+), not per **samples taken** (which would be ~10, at `sample_every=10`), the
denominator in `unique_tiles_visited / ticks_sampled` must be **the length of the tick window the
trail was collected over** (`total_ticks`), not the count of recorded position samples
(`len(trail)`). Using the sample count instead would produce a materially different, non-anchor-
matching ratio (e.g. 2 unique tiles / 20 samples = 0.10, vs. 2 / 200 = 0.01) — this distinction must
be made explicit in the implementation, not left to reuse `len(trail)` by convenience.

Recommended shape: `compute_trail_activity(unique_tiles_visited: int, ticks_sampled: int) -> float`
as a tiny pure function (`unique_tiles_visited / ticks_sampled`, zero-guarded), fed by a separate
sampling loop (below) that returns `(unique_tiles_visited, ticks_sampled)` or a richer result
dataclass carrying the raw `trail: list[tuple[int,int,int]]` for debugging/rendering reuse, matching
`density.py`'s `DensityResult`/`shape.py`'s `ShapeComponent` pattern of "raw structural facts, no
grade."

## Entity-Selection Strategy — decided, with reasoning (not left open)

**Problem restated precisely:** `render_trail.py:35`'s `next(iter(state.entities.keys()))` picks
whichever entity happens to be first in dict-insertion order — in Python 3.7+ this is deterministic
per compile, but it is an **implicit, incidental** selection (a side effect of world-assembly
insertion order), not a documented, deliberate rule. The Hard Rule "do not create hidden or implicit
durable behavior" applies directly: an implicit dict-order dependency is exactly this shape of
problem, even though the current code happens to be reproducible per seed.

**Two real candidates were weighed:**

1. **Reuse `DeterministicRNG`/`Domain`, the project's own established RNG-scoping convention**
   (`src/platform/rng.py`, already used by `WorldCompiler`'s own noise-fill draws). Rejected for this
   specific use: `DeterministicRNG`'s entire contract is *replay-critical simulation randomness* —
   every existing `Domain` value (`src/core/enums.py:168-181`) is a real gameplay concern (`SPAWN`,
   `WORLD`, `COMBAT`, `INIT`, ...). This metric is read-only, non-authoritative, post-hoc validation
   code that must never be mistaken for something the simulation itself depends on, and reusing the
   live `Kernel`'s RNG instance for a QA concern risks exactly the kind of "parallel, hidden use of an
   authoritative mechanism for a non-authoritative purpose" this project's Durable State Rule warns
   against. Minting a *new* `Domain` value (e.g. `VALIDATION`) to avoid that ambiguity is also
   rejected as scope creep — this ticket's Related Code Areas don't include `src/core/enums.py`, and
   a new domain constant is a durable, project-wide addition disproportionate to selecting one entity
   for a diagnostic trail render.
2. **A standalone, explicit, deterministic rule scoped entirely to this module — recommended.**
   `hashlib.sha256(f"{world_id}:{seed}".encode()).digest()` reduced to an index into a **sorted** list
   of active entity IDs (sorting removes the dict-insertion-order dependency the current code has).
   This is deterministic per `(world_id, seed)` (reproducible, testable), explicit and documented
   (not an incidental side effect of assembly order), and touches nothing outside this ticket's own
   module — no `DeterministicRNG`/`Domain` coupling, no risk of colliding with or appearing to
   influence real gameplay RNG draws.

**Explicitly not attempted:** filtering to "movement-capable" roles before selecting. Checked directly
— `EntityState`'s `IdentityComponent` (`src/core/state.py`) carries only a bare `role: int` enum with
no mobility/stationary flag, and `NavigationComponent.movement_mode` (`MovementMode`,
`src/core/movement_modes.py`) has no clean "never moves" value either (`WANDER`, `PURSUE`, `RETREAT`,
`HOLD`, `REPOSITION`, `INTERCEPT`, `GUARD`, `REGROUP` are all live-tactical states, not identity
traits). Building a role-allowlist would require either inventing new state that doesn't exist or a
catalog-content lookup — the latter is precisely the "data-lookup-shaped" category `PROPOSAL.md §1a`
already routed to `CatalogValidator`, out of this pure-geometry feature's scope. **Open question for
the planner, not resolved here:** whether population-wide selection (sample trail-activity for every
active entity, report min/median/etc., avoiding the "which one entity" question entirely) is a
better v1 than single-entity selection — the ticket's AC #1 phrasing ("near-zero... for the confirmed
-stuck entity pattern, and materially higher for a moving entity") reads as validating the formula
against two known trail patterns, which works identically whether the production code samples one
entity or many; single-entity selection (as decided above) is the minimal change consistent with
`render_trail.py`'s existing shape, and is the recommendation, but a population-wide variant is not
ruled out if the planner judges it worth the larger surface.

## `compute_terrain_histogram` — reuse, not reimplement

**Decision: reuse `src/rendering/density.py::compute_terrain_histogram(terrain: dict) -> dict[str,
int]` directly, do not reimplement.** Verified its signature and behavior directly (read the full
file): pure function, `dict[tuple[int,int],str] -> dict[str,int]`, no `AuthoritativeState` coupling,
no case-normalization (preserves the real corpus's confirmed `'PLAIN'`/`'plain'` casing-fragmentation
bug as distinct keys — this is deliberate per its own docstring and `shape.py`'s parallel
`group_terrain_by_type` choice, not an oversight). This is a case where reuse is unambiguously
correct, unlike `connectivity.py`'s BFS (which `shape.py`'s docstring explains could **not** be
shared as-is, because it needs one-BFS-per-terrain-type instead of one-BFS-over-the-whole-walkable-
set) — `compute_terrain_histogram` has no such per-caller variation; every consumer wants the exact
same raw per-type tile count. Importing `src.rendering.density.compute_terrain_histogram` from
`variants.py` does **not** trip the sibling "zero image/render dependency" forbidden-import test
pattern (that pattern forbids `png_writer`/`rendering.render`/`rendering.incremental`/`PIL`/`Pillow`,
not sibling pure-geometry modules — `density.py` importing `variants.py` or vice versa is exactly the
kind of intra-package reuse this project's "shared world behavior should go through systems/
registries, not scattered local hacks" architecture rule endorses).

## Module Placement

**Recommendation: `src/rendering/variants.py`**, matching the sibling pattern exactly
(`connectivity.py`, `density.py`, `shape.py` all live flat in `src/rendering/`, one file per metric
family, `TCK-20260821-VISUAL-*-METRIC` cited in each module's own docstring). Test file:
`tests/unit/rendering/test_variants.py`, matching `tests/unit/rendering/test_{connectivity,density,
shape}.py`. This ticket's own module docstring should follow the same convention the three shipped
siblings use: cite `PROPOSAL.md`'s exact line range for the TVD formula (§5c, `PROPOSAL.md:409-413`)
and state plainly that the formula "was never saved to a file previously" (per this ticket's own
Assumptions, matching the phrasing `density.py`'s docstring already used for its own never-
previously-saved nearest-neighbor-CV formula).

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract directly constrains this module's formulas —
same conclusion the three shipped siblings already reached and re-verified here: this is
non-authoritative, read-only, post-hoc validation code computed from already-compiled
`AuthoritativeState`/`terrain` data, not a simulation law. The one real engine-side interaction is
indirect: `WorldCompiler.compile()`'s noise-fill mechanism (`TCK-20260821-COMPILER-NOISE-FILL`,
`docs/mechanics/06_worldbuilding_foundation.md`'s "Noise-Fill Terrain Law" subsection) is the thing
that determines *whether* a given world's terrain is seed-varying at all — this ticket's TVD/
trail-activity code must stay correct regardless of which worlds that law currently affects, per the
seed-variance finding above, not hardcode an assumption about which worlds are/aren't affected today.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers trail-activity or
  total-variation-distance terrain-diversity (confirmed via `grep -n "trail\|variation\|tvd\|variant"`
  across the file — zero real hits). The established sibling ID sequence is `INFRA-369` (render
  determinism), `INFRA-370` (connectivity), `INFRA-371` (density CV), `INFRA-372` (shape fill-ratio/
  rotation, confirmed already present on disk) — next available ID is `INFRA-373`. Recommend a new
  entry: "total_variation_distance(h1, h2) over normalized terrain-type-proportion histograms
  reproduces the documented TVD(sandbox_world, dungeon_crawl) ≈ 0.2315 cross-spec anchor at seed 42;
  same-spec/different-seed TVD is 0.0 for dungeon_crawl (structurally seed-invariant — no module in
  its composition declares terrain_variants)" — `priority: P2`, matching `INFRA-370`/`INFRA-371`/
  `INFRA-372`'s precedent (report-only, not CI-gated, per this ticket's own Out of Scope).
Two docs were considered and explicitly excluded (neither requires an update, so neither is
listed as a bullet path above — recorded here only as prose so this section's parsed path list
stays limited to the one doc genuinely required):

The quality-scoring contract doc (path: simulation_quality/quality_scoring_contract.md, under
docs/) is not required. Re-confirms all three shipped siblings' identical judgment: grepped
directly for "variant"/"trail"/"tvd"/"rendering" — zero relevant hits, this ticket adds no SimQ
pillar and touches nothing in that contract.

The world-render-validation idea doc (path: plans/world_rendering/idea_world_render_validation.md,
under docs/) is not required. Same reasoning all three shipped siblings already established:
`tickets/todos/world-rendering-core/SEQUENCE.md` explicitly assigns final documentation of "the
finished system's real implemented contract" to the batch's last ticket,
`TCK-20260821-VISUAL-QUALITY-DOCS`. Updating it here would be premature.
- **Not required, but worth flagging separately (see Risks below) rather than silently absorbing into
  this ticket's scope:** no doc currently records that `sandbox_world`'s (and 8 other worlds')
  resolved caches are stale relative to `wolf_den_near_forest.yaml`'s `terrain_variants` field. This
  ticket's own Out of Scope explicitly excludes "making the terrain-diversity half of multi-seed
  averaging meaningful... unfiled/undecided" — the stale-cache gap is a distinct, unfiled issue in the
  same family, not something this investigation is deciding to fix, but it should not go completely
  unrecorded. Recommend the planner add one sentence to this ticket's own `investigation.md`/`plan.md`
  cross-reference trail (already satisfied by this document) rather than opening a new doc-update
  obligation — a dedicated follow-up ticket to regenerate the 9 affected `resolved/world.resolved.yaml`
  caches (and confirm no downstream golden-hash/certification test breaks) is a real, separate, future
  ticket, not this one's job to file.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry overlaps this ticket's scope (confirmed by grep, see
above). `SUB-385`/`SUB-386` in `docs/parity_ledger/substrate.yaml` (added by
`TCK-20260821-COMPILER-NOISE-FILL`/`TCK-20260821-WOLF-DEN-NOISE-MIGRATION`) cover the noise-fill
mechanism itself, not this ticket's validation-metric code — no overlap, no update needed to those
two entries. No P0 entries anywhere in the ledger are touched by this ticket's scope.

## Prior Work

- `stored_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/{investigation,plan,test_plan}.md`,
  `stored_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/{...}`,
  `stored_artifacts/TCK-20260821-VISUAL-CONNECTIVITY-METRIC/{...}` — all three read in full or in
  relevant part. Established the module-per-metric-family pattern, the frozen-dataclass result-type
  convention, the "cite PROPOSAL.md line range in the module docstring" convention, and the parity-
  ledger-ID sequencing this ticket continues.
- `tickets/done/TCK-20260821-COMPILER-NOISE-FILL.md`,
  `tickets/done/TCK-20260821-WOLF-DEN-NOISE-MIGRATION.md` (both read in full) — the source of the
  seed-variance mechanism this investigation had to verify against. Neither ticket's own scope
  included regenerating downstream `resolved/world.resolved.yaml` caches — confirmed by reading both
  "Files Changed" sections directly.
- `tests/unit/rendering/test_render_incremental.py` (read in full) — the real precedent for
  "tick a compiled `Kernel` forward N times, sample state per tick" this ticket's trail-sampling loop
  should structurally match (though trail-activity does not need `DirtySet`-filtered incremental
  rendering itself — it needs live position reads, which `render_trail.py`'s existing loop already
  does correctly).

## Risks and Open Questions

- **Blocking for the planner, not resolved here:** should this ticket's `test_variants.py` assert
  `TVD(sandbox_world_seed42, sandbox_world_seed137) == 0.0` at all, given the finding above? Two
  defensible options: (a) omit `sandbox_world` from the same-spec/different-seed test entirely, using
  only `dungeon_crawl` (robust, future-proof, matches this investigation's own recommendation), or (b)
  include `sandbox_world` too but assert against the **current, on-disk, real load path** explicitly
  and add a code comment stating plainly that this assertion is contingent on the resolved-cache
  staleness identified above and will need revisiting if/when that cache is ever regenerated. Option
  (a) is recommended (see Test Plan) as the more honest, durable choice — this document surfaces both
  so the planner makes the call deliberately, not by default.
- **Not blocking, but worth the planner's explicit decision:** single-entity vs. population-wide trail
  sampling (see Entity-Selection Strategy above) — recommendation given, not mandated.
- **Not blocking:** whether `normalize_histogram()` lives in `variants.py` itself (recommended — it's
  a one-line helper with exactly one real caller inside this module) or gets promoted to `density.py`
  alongside `compute_terrain_histogram` (rejected — `density.py`'s own docstring frames it as a
  verbatim extraction of `render_world.py`'s exact counting logic; adding a normalization step there
  would be scope creep on an already-shipped, tested sibling module for a need only this ticket has).

## Anti-Drift Hazards

- **Do not let `total_variation_distance()` grow same-spec/different-seed-aware logic**, even though
  the seed-variance finding makes such a comparison newly meaningful for `sandbox_world`-family
  worlds. AC #4 is explicit and this investigation's finding makes it more load-bearing, not less —
  the function must stay a pure, spec-blind statistical primitive; any "is this a fair cross-spec
  comparison" judgment belongs to a caller/orchestration layer this ticket does not build (`Out of
  Scope`: multi-seed averaging is `TCK-20260821-VISUAL-GRADE-SCORER`'s job).
- **Do not silently "fix" the stale `resolved/world.resolved.yaml` caches as a side effect of writing
  this ticket's tests.** It is tempting, once a test needs a genuinely seed-varying real-world
  fixture, to run `make world-resolve WORLD=sandbox_world` and commit the refreshed cache — that is a
  real, consequential change (it would also alter `sandbox_world`'s compiled entity/resource/building
  positions in ways downstream certification-corpus golden hashes may depend on) squarely outside this
  ticket's `Related Code Areas` and `Out of Scope`. If a genuinely seed-varying real-world fixture is
  needed for a test, resolve it **in-memory only** (as this investigation did) rather than mutating
  any file under `data/worlds/`.
- **Do not reuse `DeterministicRNG`/`Domain` for entity selection** without the planner explicitly
  overriding this investigation's recommendation — see Entity-Selection Strategy's reasoning above for
  why that couples a QA concern to replay-critical simulation RNG state.
- **Do not let entity-selection or trail-sampling mutate `AuthoritativeState`** — mirror
  `density.py`/`shape.py`'s own `test_does_not_mutate_authoritative_state` pattern exactly; the trail-
  sampling loop reads `kernel._state` after `kernel.tick_once()` (the tick itself legitimately mutates
  state via the authoritative pipeline) but the trail-activity computation and entity-selection
  functions themselves must be pure reads.
- **Do not skip the `compute_terrain_histogram`-returns-raw-counts vs.
  `total_variation_distance`-expects-proportions boundary.** Feeding raw counts directly into the TVD
  formula silently produces a wrong, unbounded number that would not match the 0.2315 anchor and would
  not be caught by a type checker (both are `dict[str, <number>]`).
