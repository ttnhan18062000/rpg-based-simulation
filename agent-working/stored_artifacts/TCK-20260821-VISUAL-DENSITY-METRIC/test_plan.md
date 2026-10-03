---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-DENSITY-METRIC
artifact_type: test_plan
tags: [visualization, simulation-quality, world]
---

# Test Plan — TCK-20260821-VISUAL-DENSITY-METRIC

## Regression Surface

**Unit — rendering package (must keep passing, no change expected):**
- `tests/unit/rendering/test_connectivity.py` — sibling metric, same package, must be untouched by
  this ticket's new module.
- `tests/unit/rendering/test_render_core.py`
- `tests/unit/rendering/test_render_incremental.py`
- `tests/unit/rendering/test_render_storage_integration.py`
- `tests/unit/rendering/test_render_retention_integration.py`
- `tests/unit/rendering/test_terrain_color_normalization.py`

**Unit — simulation quality (must stay green, confirms no accidental coupling):**
- `tests/unit/simulation_quality/` (full directory) — this ticket must not add a pillar or touch
  `PillarScorer`/`quality_hub`/`feed`; a green run here with zero new failures is direct evidence
  AC #4 held.

**Integration — none required.** This metric has no API route, no persistence write, no engine-tick
side effect — it is a pure function over `AuthoritativeState.entities`/`terrain`, consistent with the
connectivity sibling's own regression surface (which also required no integration-tier tests).

**Arena-combat — not applicable.** This ticket touches no combat resolution path.

## New Tests Required

All new tests live in `tests/unit/rendering/test_density.py` (new file, mirroring
`tests/unit/rendering/test_connectivity.py`'s module-per-metric convention).

1. **`test_sandbox_world_reproduces_documented_cv`**
   - Category: unit (metric-correctness — `docs/testing/test_taxonomy.md`'s category, no
     `tests/parity/` marker)
   - Verifies: `WorldRepository("data/worlds").load_world("sandbox_world")` →
     `WorldCompiler.compile(spec, seed=42)` (tick 0, no `Kernel.tick_once()` calls) → the new CV
     function reproduces `≈0.648` to the tolerance recommended in investigation.md — assert
     `round(result.cv, 3) == 0.648` (exact-to-3-decimal-places, not a wide tolerance band; see
     investigation.md's Risks section for why a loose tolerance is not warranted here).
   - Location: `tests/unit/rendering/test_density.py`

2. **`test_dungeon_crawl_reproduces_documented_cv`**
   - Category: unit (metric-correctness)
   - Verifies: same pipeline as above for `dungeon_crawl` (seed 42, tick 0) — assert
     `round(result.cv, 3) == 0.678`.
   - Location: `tests/unit/rendering/test_density.py`

3. **`test_population_stdev_not_sample_stdev`**
   - Category: unit (regression guard against the specific, confirmed-real formula ambiguity)
   - Verifies: a small synthetic fixture (e.g. 3-4 entities at known, hand-computed coordinates)
     where population-std and sample-std produce visibly different CV values; asserts the function's
     result matches the population-std hand-computation, not the sample-std one. This is the direct
     regression guard for investigation.md's documented finding that `statistics.stdev()` (ddof=1)
     silently produces a wrong, non-matching number (0.667 vs 0.648 for `sandbox_world`).
   - Location: `tests/unit/rendering/test_density.py`

4. **`test_two_entities_minimum_nn_distance`** (edge case)
   - Category: unit
   - Verifies: with exactly 2 entities, each entity's nearest neighbor is unambiguously the other one
     — a minimal, hand-verifiable fixture that doesn't depend on corpus data.
   - Location: `tests/unit/rendering/test_density.py`

5. **`test_inactive_entities_excluded_from_cv`** (edge case / filter correctness)
   - Category: unit
   - Verifies: an entity with `lifecycle.active == False` (or equivalent `EntityState.active`
     property returning `False`) does not affect the CV computation — construct a small fixture with
     one inactive entity positioned far from the rest and confirm its presence/absence doesn't change
     the result.
   - Location: `tests/unit/rendering/test_density.py`

6. **`test_terrain_histogram_sums_to_terrain_tile_count`** (AC #2)
   - Category: unit
   - Verifies: for a synthetic terrain fixture with a known mix of terrain-type strings (including a
     deliberately mixed-case pair, e.g. `"PLAIN"` and `"plain"`, mirroring the real casing-bug
     evidence from `render_world.py`), `sum(histogram.values()) == len(terrain)` exactly, and that
     `"PLAIN"`/`"plain"` remain **distinct** keys (raw values, no normalization) — directly guards the
     Anti-Drift Hazard about not silently normalizing histogram keys during extraction.
   - Location: `tests/unit/rendering/test_density.py`

7. **`test_dungeon_crawl_histogram_matches_terrain_tile_count`** (AC #2, real-corpus)
   - Category: unit (metric-correctness, real corpus)
   - Verifies: same sum-invariant as above, but against the real compiled `dungeon_crawl` state
     (`state.terrain`), confirming the invariant holds on real, non-synthetic data too.
   - Location: `tests/unit/rendering/test_density.py`

8. **`test_density_module_has_zero_image_or_render_dependency`** (AC #3, Tier-0 pure-data-path guard)
   - Category: architecture guard (import-boundary static check, same shape as the "no PillarScorer
     subclass" guard below)
   - Verifies: inspect `src/rendering/density.py`'s module-level imports (e.g. via `ast.parse` on the
     source file, or a simple `import density; inspect.getsource(density)` string-scan for forbidden
     tokens) and assert none of `src.rendering.png_writer`, `src.rendering.render`,
     `src.rendering.incremental`, `PIL`/`Pillow`, or any other image-writing module is imported. This
     proves the module is reachable and computable with zero rendering/image dependency, satisfying
     AC #3's "Tier-0 pure-data path, zero image/render dependency" literally, not just by absence of
     a failing test.
   - Location: `tests/unit/rendering/test_density.py`

9. **`test_density_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`** (AC #4)
   - Category: architecture guard (negative/static import check)
   - Verifies: statically inspects `src/rendering/density.py`'s source (AST-based, not a runtime
     import-and-introspect, to avoid false negatives from lazy/deferred imports) for two forbidden
     patterns: (a) any class definition with `PillarScorer` (or
     `src.simulation_quality.scorers.base.PillarScorer`) in its base-class list; (b) any `import`/
     `from ... import ...` statement referencing `src.simulation_quality` or
     `src.observability.events` (the exact `ObservabilityEventEnvelope` import path cited in
     investigation.md). Fails loudly if either pattern is found, directly enforcing AC #4's negative
     requirement rather than relying on the absence of a positive test.
   - Location: `tests/unit/rendering/test_density.py`

10. **`test_does_not_mutate_authoritative_state`** (architecture guard, mirrors
    `test_connectivity.py`'s own guard of the same name)
    - Category: architecture guard
    - Verifies: calling the CV/histogram functions twice against the same `entities`/`terrain`
      fixture produces identical results both times, and the input `dict`/collection contents are
      byte-for-byte unchanged after the calls (`terrain_before == terrain` style comparison) — proves
      read-only logic did not mutate live state, per CLAUDE.md's Architecture Rule/Testing Rule.
    - Location: `tests/unit/rendering/test_density.py`

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/rendering/ -v
.venv/bin/python3 -m pytest tests/unit/simulation_quality/ -v
```

Both directories, not individual cherry-picked files — matches this repo's own established scoping
convention (bare test directory in the pytest command, per prior hand-orchestration feedback) and
mirrors exactly what `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`'s own test plan scoped to. Never
`pytest tests/`.

## Anti-Drift Test Guards

- **Test 3 (`test_population_stdev_not_sample_stdev`) is the single most important anti-drift guard
  in this plan** — it is the only test that would catch a silent regression from population-std to
  sample-std (e.g. an implementer reaching for `statistics.stdev()` instead of `statistics.pstdev()`
  out of habit), which produces a plausible-looking but wrong number (0.667 vs 0.648) that a looser
  tolerance-based reproduction test alone might not catch.
- **Test 6/9's raw-key preservation assertion** guards against a well-intentioned but wrong
  "cleanup" — normalizing `'PLAIN'`/`'plain'` into one key during extraction would still pass a naive
  sum-invariant check but would silently diverge from the cited prototype evidence and from what
  `render_world.py`'s original `terrain_histogram` actually returns.
- **Test 8/9 (architecture guards)** are the direct, literal enforcement of AC #3 and AC #4 — without
  them, "zero image dependency" and "no PillarScorer subclass" are only true by omission and could
  silently regress in a future edit with no test catching it, exactly the failure mode CLAUDE.md's
  Architecture Rule test-guard requirement exists to prevent.
- **Test 5 (inactive-entity exclusion)** guards against scope creep where a future edit accidentally
  starts counting dead/inactive entities into the CV, which would silently change every corpus-world
  reproduction number without any of the exact-value tests (1/2) necessarily catching it if the drift
  is small enough to round to the same 3 decimal places on some worlds but not others.
- **Regression surface `tests/unit/simulation_quality/`** — running the full existing SimQ unit suite
  unchanged is itself an anti-drift guard: since this ticket must not touch any SimQ file, a still-green
  SimQ suite after this ticket's diff lands is direct evidence no accidental coupling was introduced,
  independent of the static AC #4 guard.

## Deviations

- **Path correction (implementer, Step 3 verification):** this file's "Scoped Pytest Commands" and
  Regression Surface sections name `tests/unit/simulation_quality/`. That path does not exist in the
  repo — the real directory is `tests/simulation_quality/` (no `unit/` prefix), confirmed via `find`.
  Ran `PYTHONPATH=. .venv/bin/python3 -m pytest tests/simulation_quality/ -q` instead: 499 passed, 12
  skipped, 41 failed. All 41 failures are in `test_grade_regression.py::test_grade_within_anchor_band*`
  and are pre-existing (unrelated to this ticket's diff, which touches zero files under
  `src/simulation_quality/` or `tests/simulation_quality/`) — root cause confirmed directly from one
  failure's assertion message: a known PROGRESSION-pillar score-tolerance drift tied to
  `detection_params.yaml`'s `progression_frozen_by_tick=200` threshold rule, not a density/rendering
  coupling issue. The still-green 499/499 remainder of the suite is the actual anti-coupling evidence
  for AC #4. See `tickets/inprogress/TCK-20260821-VISUAL-DENSITY-METRIC.md`'s Implementation Notes for
  the full account.
