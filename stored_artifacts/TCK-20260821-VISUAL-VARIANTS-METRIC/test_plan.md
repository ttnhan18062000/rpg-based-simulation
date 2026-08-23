---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-VARIANTS-METRIC
artifact_type: test_plan
tags: [visualization, simulation-quality, determinism, world]
---

# Test Plan — TCK-20260821-VISUAL-VARIANTS-METRIC

## Regression Surface

Existing tests that must keep passing, scoped to the affected domains — nothing in this ticket's
scope touches `WorldCompiler`, `WorldAssemblyResolver`, or any world-content YAML, so the noise-fill
regression surface is a read-only check, not a change surface:

- **unit (rendering siblings, must stay green and unmodified):**
  - `tests/unit/rendering/test_density.py`
  - `tests/unit/rendering/test_shape.py`
  - `tests/unit/rendering/test_connectivity.py`
  - `tests/unit/rendering/test_render_core.py`
  - `tests/unit/rendering/test_terrain_color_normalization.py`
- **architecture guard:**
  - `tests/architecture/test_rendering_zero_new_dependency_guard.py` (must keep passing with the new
    `src/rendering/variants.py` file included in its `src/rendering` walk — no third-party import may
    be added)
- **integration (the noise-fill mechanism this ticket's seed-variance finding depends on — read-only
  verification that these still hold, not a change surface):**
  - `tests/integration/worldassembly/test_real_content_world_modules.py`
  - `tests/integration/worldassembly/test_wolf_den_noise_migration.py`
  - `tests/unit/worldbuilding/test_world_compiler.py`
  - `tests/certification/test_world_compile_determinism.py` (confirms unrelated worlds' golden hashes
    are still unaffected — this ticket must not be the reason this ever needs re-running for real, but
    it is cheap insurance given how directly this ticket's own investigation depended on the noise-fill
    mechanism's behavior)

## New Tests Required

All new tests live in `tests/unit/rendering/test_variants.py` unless noted, mirroring
`test_density.py`/`test_shape.py`'s file layout and fixture style (synthetic dict fixtures for pure-
function unit tests, real `WorldRepository`/`WorldCompiler.compile()` calls only for corpus-
reproduction tests).

1. **`test_total_variation_distance_reproduces_sandbox_dungeon_anchor`**
   Category: unit (real-corpus reproduction, same shape as `test_density.py::
   test_sandbox_world_reproduces_documented_cv`).
   Verifies: loading `sandbox_world` and `dungeon_crawl` via the real, on-disk
   `WorldRepository("data/worlds").load_world(...)` → `WorldCompiler.compile(spec, seed=42)` path (no
   in-memory fresh-resolve bypass — this must exercise the exact path production code uses),
   normalizing both terrain histograms, and asserting `round(total_variation_distance(h1, h2), 4) ==
   0.2316` (the verified value is `0.23161981243456373`; assert against the precise value, not the
   PROPOSAL.md-rounded `0.2315`, to avoid a test that passes by coincidence of rounding direction —
   document the exact anchor value inline, citing this investigation).

2. **`test_total_variation_distance_formula_on_synthetic_histograms`**
   Category: unit.
   Verifies: the raw formula against hand-computed synthetic proportions (e.g. `h1={"A":1.0}`,
   `h2={"B":1.0}` → TVD `1.0`; `h1==h2` → TVD `0.0`; a partial-overlap case with a hand-computed
   expected value) — isolates the formula itself from any real-corpus data, matching
   `test_shape.py::test_fill_ratio_formula_on_synthetic_shapes`'s role.

3. **`test_total_variation_distance_same_spec_different_seed_is_zero_for_dungeon_crawl`**
   Category: unit (real-corpus reproduction).
   Verifies AC #3, anchored to `dungeon_crawl` **specifically, not `sandbox_world`** — per this
   ticket's investigation, `dungeon_crawl`'s composition (`ruins_mystery_quest`,
   `goblin_camp_conflict`, `old_mine_resource_loop`, `scalable_bandit_camp`) contains zero modules
   declaring `terrain_variants`, so it is structurally seed-invariant regardless of resolved-cache
   freshness — a durable anchor, unlike `sandbox_world`. Compiles `dungeon_crawl` at seed 42 and seed
   137 via the real on-disk load path, normalizes both histograms, asserts
   `total_variation_distance(h1, h2) == 0.0` exactly (not `pytest.approx` — the underlying terrain
   dicts are asserted byte-identical first, so the TVD value must be exactly `0.0`, not merely close).
   Test docstring must state explicitly, in-line, why `dungeon_crawl` was chosen over `sandbox_world`
   (cite this investigation's stale-resolved-cache finding) so a future reader does not "fix" the
   anchor choice back to `sandbox_world` without re-reading the reasoning.

4. **`test_variants_module_does_not_encode_same_spec_seed_variance_as_a_signal`**
   Category: architecture guard (AST-based, mirrors `test_shape.py`'s
   `test_shape_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` pattern of
   scanning the module source directly, not behavioral).
   Verifies AC #4 structurally: `ast.parse(variants.py)` contains no function whose signature or body
   references `seed` as a comparison axis paired with a fixed `world_id`/`spec` — concretely, asserts
   `total_variation_distance`'s own parameter names are exactly `h1`, `h2` (or equivalent
   histogram-only names), never `seed`/`world_id`/`spec_a`/`spec_b`, confirming by construction that
   the function itself cannot special-case same-spec comparisons even if a future caller tried to feed
   it one.

5. **`test_compute_terrain_histogram_is_reused_not_reimplemented`**
   Category: architecture guard.
   Verifies the reuse decision from investigation.md: `ast.parse(variants.py)` contains an
   `ImportFrom` node with `module == "src.rendering.density"` and `"compute_terrain_histogram"` among
   its imported names, and — separately — that `variants.py` does **not** define its own function
   whose body re-implements the `histogram[tval] = histogram.get(tval, 0) + 1` counting loop (grep-
   style substring check on the module source for a second `terrain.values()` iteration pattern is an
   acceptable, simpler proxy for this half of the assertion if the AST check proves too brittle —
   planner's call).

6. **`test_normalize_histogram_converts_counts_to_proportions_summing_to_one`**
   Category: unit.
   Verifies: given a synthetic raw-count histogram (e.g. `{"PLAIN": 3, "FOREST": 1}`), the
   normalization helper returns proportions summing to `1.0` (within float tolerance) and preserves
   relative ratios (`PLAIN: 0.75, FOREST: 0.25`); a zero-total/empty-input case returns `{}` (or
   another explicitly-documented sentinel) rather than raising `ZeroDivisionError`.

7. **`test_trail_activity_near_zero_for_stuck_pattern`**
   Category: unit.
   Verifies AC #1's stuck-entity half: a synthetic trail fixture matching `PROPOSAL.md`'s own real
   observed data shape (positions clustered in a 2-tile set across a 100+ "tick window" denominator —
   e.g. `unique_tiles_visited=2, ticks_sampled=100` → ratio `0.02`), asserting the result falls in the
   documented "~2-3 tiles/100+ ticks" near-zero band. Must NOT construct the ratio from
   `len(trail_samples)` (the count of recorded samples) — see investigation.md's denominator finding —
   the test fixture must make this distinction explicit (e.g. `sample_every=10` over `total_ticks=100`
   yielding only 10 recorded samples, but `ticks_sampled` passed to the formula is `100`, not `10`),
   so a future implementation swap to the wrong denominator fails this test visibly.

8. **`test_trail_activity_materially_higher_for_moving_pattern`**
   Category: unit.
   Verifies AC #1's moving-entity half: a synthetic trail visiting many distinct tiles across the same
   tick-window length used in test 7, asserting the resulting ratio is materially higher (e.g. an
   order of magnitude) than the stuck-pattern result — a relative, not absolute, assertion, matching
   the AC's own comparative phrasing ("materially higher for a moving entity").

9. **`test_select_trail_entity_is_deterministic_per_world_and_seed`**
   Category: unit.
   Verifies the entity-selection decision from investigation.md: calling the selection function twice
   with the same `(world_id, seed, active_entity_ids)` inputs returns the same entity ID; calling it
   with a different `seed` (same `world_id`/entity set) can return a different entity ID (not asserted
   to always differ — only that the function is seed-sensitive, not seed-blind); calling it with the
   entity-ID set presented in two different insertion orders (e.g. a dict built in reverse) returns the
   **same** result both times — the regression-guard for the exact bug being fixed (implicit
   dict-order dependency).

10. **`test_select_trail_entity_only_considers_active_entities`**
    Category: unit.
    Verifies: an inactive entity (mirroring `density.py`'s own
    `test_inactive_entities_excluded_from_cv` convention) is never selectable, even if it would
    otherwise be chosen by the deterministic rule — constructs a fixture where the deterministic index
    would land on an inactive entity absent filtering, confirming the implementation filters before
    selecting, not after.

11. **`test_render_trail_prototype_and_variants_module_selection_agree`** *(optional, planner's call —
    lower priority than 1-10)*
    Category: integration.
    If `render_trail.py`'s own hardcoded selection is ever updated in this ticket to delegate to the
    new `select_trail_entity` (rather than left untouched as a frozen prototype, per this project's
    "experiments/ sandbox stays runnable, not necessarily rewritten" convention — planner's call
    whether `render_trail.py` is in scope to touch at all, since it is listed only under Related Code
    Areas as prior art to read, not explicitly required to be edited) — confirms both call sites
    produce the same entity ID for the same world/seed.

12. **`test_variants_module_has_zero_image_or_render_dependency`**
    Category: architecture guard (exact pattern match, `test_density.py:130-145` /
    `test_shape.py:257-273`).
    Verifies: `ast.parse(variants.py)` contains no `Import`/`ImportFrom` node naming `png_writer`,
    `rendering.render`, `rendering.incremental`, `PIL`, or `Pillow`.

13. **`test_variants_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`**
    Category: architecture guard (exact pattern match, `test_density.py:147-166` /
    `test_shape.py:236-256` — the sibling equivalent of what this ticket's Assumptions section calls
    out as "an architecturally-independent SimQ-sibling").
    Verifies: no `ClassDef` in `variants.py` has `PillarScorer` among its base names; no
    `Import`/`ImportFrom` node names anything containing `"simulation_quality"` or
    `"observability.events"`.

14. **`test_does_not_mutate_authoritative_state`**
    Category: unit (exact pattern match, `test_density.py:168-188` / `test_shape.py`'s equivalent).
    Verifies: calling `total_variation_distance`, `normalize_histogram`, `compute_trail_activity`, and
    `select_trail_entity` twice each on identical inputs produces identical outputs, and the input
    dicts/sequences are unchanged (`==` before/after) after each call.

## Scoped Pytest Commands

```
pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v -m "not slow"
```

Regression-surface confirmation (the noise-fill mechanism this ticket's seed-variance finding
depends on — cheap insurance, not expected to change, run once before Verify):

```
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/integration/worldassembly/test_wolf_den_noise_migration.py \
       tests/unit/worldbuilding/test_world_compiler.py \
       tests/certification/test_world_compile_determinism.py \
       -v -m "not slow"
```

Never `pytest tests/` — both commands above are scoped to the rendering-metric domain and the
noise-fill domain this ticket's own empirical work depended on, per the Testing Rule.

## Anti-Drift Test Guards

- **Test 3's `dungeon_crawl`-not-`sandbox_world` anchor choice is itself the primary anti-drift guard
  for this entire ticket.** If a future implementer or planner reverts this to `sandbox_world` "for
  simplicity" without re-reading investigation.md, that test will start failing the moment any
  unrelated session runs `make world-resolve WORLD=sandbox_world` — the in-line docstring citation
  (test 3) exists specifically so that failure is immediately traceable to this investigation's known
  cause, not mistaken for a real regression in `total_variation_distance` itself.
- **Test 4 is the structural guard for AC #4** — catches, at review time rather than at some future
  runtime surprise, any refactor that gives `total_variation_distance` (or a sibling helper in the
  same module) a `seed`/`world_id` parameter, which would be the first step toward the exact "same-
  spec/different-seed treated as a diversity signal" architecture violation the ticket's Scope
  explicitly forbids.
- **Test 5 is the anti-drift guard against silently re-implementing `compute_terrain_histogram`** —
  catches a future edit that duplicates the counting loop locally (e.g. during an unrelated
  refactor) instead of continuing to import the shared sibling function, which would silently
  reintroduce a second source of truth for terrain counting logic this project's "shared world
  behavior should go through systems/registries, not scattered local hacks" rule exists to prevent.
- **Test 7's explicit `sample_every != ticks_sampled`-denominator fixture is the anti-drift guard for
  the trail-activity formula's most likely silent-regression path** — a future refactor that simplifies
  the sampling loop to "just use `len(trail)`" (the more obvious-looking implementation) would still
  compile and run, but would silently stop matching the cited "~2-3 tiles/100+ ticks" evidence; this
  test fails loudly instead.
- **Test 9's insertion-order-reversal check is the direct regression guard for the exact bug this
  ticket's Scope names** (`render_trail.py`'s hardcoded "first entity in dict") — without it, a future
  edit could reintroduce a `next(iter(...))`-shaped implicit-order dependency inside
  `select_trail_entity` itself and every other test would still pass, since most fixtures build dicts
  in a fixed order already.
- **Tests 12/13 close the exact gap this investigation found in the sibling pattern**
  (`connectivity.py` never got its own in-file forbidden-pattern tests, only `density.py`/`shape.py`
  did) — this ticket's module should not repeat that omission.
