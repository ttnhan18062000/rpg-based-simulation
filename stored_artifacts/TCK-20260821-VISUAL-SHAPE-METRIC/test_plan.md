---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-SHAPE-METRIC
artifact_type: test_plan
tags: [visualization, simulation-quality, world]
---

# Test Plan — TCK-20260821-VISUAL-SHAPE-METRIC

## Regression Surface

**Unit — rendering package (must keep passing, no change expected):**
- `tests/unit/rendering/test_connectivity.py` — sibling metric, same package, must be untouched.
- `tests/unit/rendering/test_density.py` — sibling metric, same package, must be untouched.
- `tests/unit/rendering/test_render_core.py`
- `tests/unit/rendering/test_render_incremental.py`
- `tests/unit/rendering/test_render_storage_integration.py`
- `tests/unit/rendering/test_render_retention_integration.py`
- `tests/unit/rendering/test_terrain_color_normalization.py`

**Unit — simulation quality (must stay green, confirms no accidental coupling):**
- `tests/simulation_quality/` (full directory, correct real path — not `tests/unit/simulation_quality/`,
  which does not exist; confirmed directly via `ls`, matching the density sibling's own
  post-implementation path correction). This ticket must not add a pillar or touch
  `PillarScorer`/`quality_hub`/`feed`; a still-green run here with zero new failures is direct
  evidence AC #5 held. Note: the density sibling's own Deviations record 41 pre-existing failures
  in `test_grade_regression.py::test_grade_within_anchor_band*`, unrelated to this ticket's diff
  (a known `PROGRESSION`-pillar score-tolerance drift) — expect the same pre-existing failure count
  here; do not treat it as a regression this ticket caused, and do not attempt to fix it as part of
  this ticket's scope.

**Integration — none required.** This metric has no API route, no persistence write, no engine-tick
side effect — a pure function over `AuthoritativeState.terrain`, consistent with both prior
siblings' own regression surface (neither required integration-tier tests).

**Arena-combat — not applicable.** This ticket touches no combat resolution path.

## New Tests Required

All new tests live in `tests/unit/rendering/test_shape.py` (new file, mirroring
`test_connectivity.py`/`test_density.py`'s module-per-metric convention).

1. **`test_connected_component_labeling_splits_disjoint_same_type_patches`**
   - Category: unit (metric-correctness)
   - Verifies: a small synthetic terrain fixture with two same-terrain-type patches separated by a
     gap (or a different terrain type) produces 2 components, not 1 — the direct regression guard
     for the exact bug `PROPOSAL.md §5c` found and fixed (per-terrain-type aggregation without
     connectivity is wrong). This is the single most important correctness guard in this plan.
   - Location: `tests/unit/rendering/test_shape.py`

2. **`test_dungeon_crawl_forest_is_two_components_of_1116_tiles_each`** (AC #1)
   - Category: unit (metric-correctness, real corpus)
   - Verifies: `WorldRepository("data/worlds").load_world("dungeon_crawl")` →
     `WorldCompiler.compile(spec, seed=42)` (tick 0, no `Kernel.tick_once()` calls, matching
     `test_connectivity.py`'s established invocation shape) → grouping `state.terrain` by raw
     terrain-string value and running connected-component labeling on the `forest`-keyed tile set
     produces exactly 2 components, each exactly 1,116 tiles — exact equality, no tolerance
     (verified directly this session; the pipeline is confirmed fully deterministic).
   - Location: `tests/unit/rendering/test_shape.py`

3. **`test_dungeon_crawl_per_component_fill_ratios_match_documented_evidence`** (AC #2)
   - Category: unit (metric-correctness, real corpus)
   - Verifies: same `dungeon_crawl` compile as above; asserts
     `round(cave_component.fill_ratio, 3) == 0.980`,
     `round(forest_c0.fill_ratio, 3) == 1.000`, `round(forest_c1.fill_ratio, 3) == 1.000`,
     `round(ruin_component.fill_ratio, 3) == 1.000` — exact-to-3-decimal-places (matching this
     batch's own established exact-assertion convention for a confirmed fully-deterministic
     pipeline; verified directly this session to reproduce to full float precision, not just 3dp).
   - Location: `tests/unit/rendering/test_shape.py`

4. **`test_fill_ratio_formula_on_synthetic_shapes`** (formula regression guard)
   - Category: unit
   - Verifies: hand-computable synthetic fixtures independent of corpus data — a perfect 4x4 square
     (fill_ratio == 1.0), an L-shape inscribed in a bounding box with a known excluded corner
     (fill_ratio < 1.0, hand-computed exact value), and a single-tile component (fill_ratio == 1.0,
     1x1 bounding box) — guards the `tiles / bounding_box_area` formula itself independent of any
     real-world data drift.
   - Location: `tests/unit/rendering/test_shape.py`

5. **`test_forest_components_detected_as_90_degree_rotation`** (AC #3)
   - Category: unit (metric-correctness, real corpus)
   - Verifies: same `dungeon_crawl` compile; running the rotation-detection function on the two real
     `FOREST` components returns a positive match — reproduces the documented finding that component
     1 (bbox `(95,20)-(125,55)`, 31×36) is a 90°-rotation-related match of component 0 (bbox
     `(50,30)-(85,60)`, 36×31).
   - Location: `tests/unit/rendering/test_shape.py`

6. **`test_rotation_detection_rejects_non_rotated_shapes`** (negative case, formula regression guard)
   - Category: unit
   - Verifies: two synthetic components with swapped bounding-box dimensions but genuinely different
     internal tile patterns (e.g. an L-shape vs. its non-matching mirror) are correctly reported as
     *not* a rotation match — guards against a degenerate implementation that only checks
     bounding-box dimension-swap and never actually compares tile-set contents (which would produce
     false positives on any two same-area, dimension-swapped shapes).
   - Location: `tests/unit/rendering/test_shape.py`

7. **`test_rotation_detection_on_solid_rectangles_is_not_over_claimed`** (documents the
   investigation's own caveat)
   - Category: unit
   - Verifies: for two solid (fill_ratio == 1.0) same-area rectangles with swapped dimensions, the
     transpose test, rotate-90-CW test, and rotate-90-CCW test all independently return a match —
     a direct regression guard for investigation.md's documented finding that solid rectangles don't
     distinguish "true rotation" from other dimension-swapping symmetries, so the implementation and
     its docstring must not claim rotation-specificity this case doesn't actually establish.
   - Location: `tests/unit/rendering/test_shape.py`

8. **`test_min_component_size_filter_excludes_small_fragments`** (synthetic, since no real corpus
   world currently has a sub-20-tile component to exercise this)
   - Category: unit (edge case)
   - Verifies: a synthetic terrain fixture with one real biome patch (≥20 tiles) and one deliberately
     tiny noise fragment of the same terrain type but disconnected (<20 tiles, e.g. 3 tiles) — the
     corpus-sweep-shaped aggregation function excludes the small fragment from its reported component
     list/count while still correctly reporting the real patch. Directly documents (per
     investigation.md's Risks section) that this filter is untestable against real corpus data today
     and must be covered synthetically.
   - Location: `tests/unit/rendering/test_shape.py`

9. **`test_plain_and_road_excluded_case_insensitively`** (synthetic, formula-scope guard)
   - Category: unit (edge case)
   - Verifies: a synthetic terrain fixture containing `"PLAIN"`, `"plain"`, `"ROAD"`, `"road"`, and
     one real biome type (e.g. `"cave"`) — the corpus-sweep-shaped aggregation excludes all four
     casing variants of `PLAIN`/`ROAD` from its component list while including the biome component,
     directly guarding investigation.md's recommended `tval.upper() in {"PLAIN", "ROAD"}`
     case-insensitive exclusion test (as opposed to a brittle hardcoded 4-string list).
   - Location: `tests/unit/rendering/test_shape.py`

10. **`test_corpus_wide_sweep_every_below_threshold_component_is_forest`** (AC #4)
    - Category: unit (metric-correctness, real full corpus)
    - Verifies: runs the fill-ratio sweep (≥20 tiles, PLAIN/ROAD excluded) across every world
      `WorldRepository("data/worlds").list_worlds()` returns (the full current corpus — 21 worlds as
      of this investigation, not a hardcoded count) and asserts that every single component scoring
      below 0.95 has terrain type `forest` (case-insensitive) — the qualitative invariant that holds
      identically whether the corpus has 18, 21, or more worlds, per investigation.md's
      recommendation to the planner. This is the version of AC #4 that does not silently break the
      next time a new world is added to `data/worlds/`.
    - Location: `tests/unit/rendering/test_shape.py`

11. **`test_corpus_wide_sweep_historical_18_world_subset_matches_26_of_33`** (AC #4, literal
    historical reproduction — **planner must confirm this test is wanted before implementation;
    see investigation.md's Risks section for the (a)/(b) choice this depends on**)
    - Category: unit (metric-correctness, real corpus, historical-reproduction)
    - Verifies: if the planner chooses interpretation (a) (reproduce the literal `26/33`/`78.8%`
      figure), this test explicitly excludes exactly `{"lifecycle_full_coverage_world",
      "quest_dense_frontier", "simq_scale_stress_seed42"}` from the current corpus (with a code
      comment citing this investigation's finding that these 3 worlds did not exist when
      `PROPOSAL.md`'s corpus sweep was performed) and asserts `total_components == 33`,
      `ge_95_count == 26`. If the planner chooses interpretation (b), **do not write this test at
      all** — Test 10 alone covers AC #4's real, durable content.
    - Location: `tests/unit/rendering/test_shape.py`

12. **`test_shape_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`** (AC #5)
    - Category: architecture guard (negative/static import check)
    - Verifies: statically inspects `src/rendering/shape.py`'s source (AST-based, matching the
      density sibling's own precedent, to avoid false negatives from lazy/deferred imports) for two
      forbidden patterns: (a) any class definition with `PillarScorer` in its base-class list; (b)
      any `import`/`from ... import ...` statement referencing `src.simulation_quality` or
      `src.observability.events`. Fails loudly if either pattern is found, directly enforcing AC #5.
    - Location: `tests/unit/rendering/test_shape.py`

13. **`test_shape_module_has_zero_image_or_render_dependency`** (Scope's "pure
    visualization/geometry computation only" requirement, mirroring the density sibling's AC #3
    guard)
    - Category: architecture guard
    - Verifies: `src/rendering/shape.py` imports none of `src.rendering.png_writer`,
      `src.rendering.render`, `src.rendering.incremental`, or any image-writing library.
    - Location: `tests/unit/rendering/test_shape.py`

14. **`test_does_not_mutate_authoritative_state`** (architecture guard, mirrors both siblings' guard
    of the same name)
    - Category: architecture guard
    - Verifies: calling the shape functions twice against the same `terrain` fixture produces
      identical results both times, and the input dict's contents are byte-for-byte unchanged after
      the calls — proves read-only logic did not mutate live state, per CLAUDE.md's Architecture
      Rule/Testing Rule.
    - Location: `tests/unit/rendering/test_shape.py`

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/rendering/ -v
.venv/bin/python3 -m pytest tests/simulation_quality/ -q
```

Both directories, not individual cherry-picked files — matches this repo's own established scoping
convention and both prior sibling tickets' own test plans. Never `pytest tests/`.

## Anti-Drift Test Guards

- **Test 1 is the single most important guard in this plan** — it is the direct regression test for
  the exact bug `PROPOSAL.md §5c` found and fixed (per-terrain-type aggregation without connectivity
  labeling). Without it, a well-intentioned "simplification" back to per-terrain-type bounding boxes
  would silently reproduce the pre-fix, wrong `FOREST=0.716` behavior while still passing a naive
  fill-ratio-formula test.
- **Test 7 guards against over-claiming rotation-specificity** the real evidence doesn't establish
  for solid-rectangle pairs — without it, a docstring or downstream consumer could incorrectly treat
  "transpose match" as proof of a literal 90° rotation for every component pair, when for solid
  rectangles it is really "any dimension-swapping symmetry matches."
- **Test 6 is the negative counterpart to Test 5** — without it, a degenerate implementation that
  only checks bounding-box dimension-swap (and never actually compares tile-set contents) would pass
  Test 5 while producing false positives on every same-area, dimension-swapped shape pair, silently
  making the "rotation detection" feature meaningless.
- **Tests 8/9 (synthetic edge cases for the min-size filter and the PLAIN/ROAD exclusion)** are the
  only guards for two documented parameters that the real corpus currently cannot exercise (no real
  component is under 20 tiles; the exclusion casing variants only matter if a future world introduces
  a new casing) — without them, both parameters could silently regress (or be silently deleted as
  "dead code," since nothing in the real-corpus tests would notice) with zero test failure.
- **Test 10 vs. Test 11** — Test 10 is the durable, corpus-size-independent guard; Test 11 (if
  written at all, per the planner's choice) is explicitly fragile by design and documents exactly why
  in its own code comment, so it fails loudly and legibly (not silently) the next time a world is
  added to `data/worlds/`, rather than either breaking without explanation or silently drifting.
- **Test 12 is the direct, literal enforcement of AC #5** — without it, "no PillarScorer subclass, no
  SimQ import" is only true by omission and could silently regress in a future edit with no test
  catching it, exactly the failure mode CLAUDE.md's Architecture Rule test-guard requirement exists
  to prevent.
- **Regression surface `tests/simulation_quality/`** — a still-green run (modulo the documented
  41 pre-existing, unrelated `test_grade_regression.py` failures) after this ticket's diff lands is
  itself an anti-drift guard, independent of Test 12's static AC #5 check: it proves no accidental
  coupling was introduced at runtime, not just at the import-graph level.
