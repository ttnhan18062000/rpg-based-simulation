---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-GRADE-SCORER
artifact_type: test_plan
tags: [visualization, simulation-quality, world]
---

# Test Plan — TCK-20260821-VISUAL-GRADE-SCORER

## Regression Surface

**Unit — sibling metric modules this ticket consumes (must not be modified, must keep passing):**
- `tests/unit/rendering/test_connectivity.py`
- `tests/unit/rendering/test_density.py`
- `tests/unit/rendering/test_shape.py`
- `tests/unit/rendering/test_variants.py`
- `tests/unit/rendering/test_render_core.py`
- `tests/unit/rendering/test_render_incremental.py`
- `tests/unit/rendering/test_terrain_color_normalization.py`

**Architecture — package-wide guards this ticket's new module(s) must also satisfy:**
- `tests/architecture/test_rendering_zero_new_dependency_guard.py` (stdlib-only import guard, walks
  all of `src/rendering/` — the new module(s) fall under this automatically, no test change needed,
  but must genuinely pass: no numpy/PIL/pydantic/third-party imports).

**Integration/storage — unrelated but same-package, confirm no accidental import-graph coupling:**
- `tests/unit/rendering/test_render_retention_integration.py`
- `tests/unit/rendering/test_render_storage_integration.py`

**SimQ regression surface — must stay completely unaffected (proves independence, not just claims
it):**
- `tests/simulation_quality/test_report.py` (grade assignment / normalized-score formula, including
  `test_combat_grade_stable_across_tick_counts_for_same_activity`, INFRA-255/COMB-293's own test)
- `tests/simulation_quality/test_weights.py` (`ScoringWeights.load` / `GRADE_THRESHOLDS` loading)
- `tests/simulation_quality/test_grade_regression.py` (grade anchor regression suite)

## New Tests Required

Per acceptance criteria, one entry per required new test:

- **Grade assignment reuses the exact reused threshold table**
  - Category: unit
  - Verifies: given synthetic normalized scores at and around each boundary (e.g. `2.0`, `2.0001`,
    `0.5`, `0.5001`, `0.0`, `0.0001`, `-0.5`, `-0.5001`, `-1.0`, `-1.0001`, and one comfortably inside
    each band), the new `assign_grade`-equivalent function returns exactly
    `S`/`A`/`B`/`C`/`D`/`F` matching SimQ's own `_assign_grade` semantics (`>` not `>=`, strict
    descending ladder — mirror `src/simulation_quality/quality_report.py::_assign_grade`'s own
    boundary behavior exactly, since AC #1 requires *the exact same table*, which implies the exact
    same comparison semantics, not just the same numeric values).
  - Where: `tests/unit/rendering/test_grading.py` (or `tests/unit/rendering/test_<chosen_module_name>.py`
    if the planner picks a different module name)

- **Grade thresholds are sourced from a config file, never hardcoded**
  - Category: unit / architecture guard
  - Verifies: an AST-walk or direct-value test proving the grading module's source contains no
    inline numeric literals for `2.0`/`0.5`/`0.0`/`-0.5`/`-1.0` used as thresholds (only as, e.g.,
    test-fixture inputs or unrelated constants) — mirrors SimQ's own §4.8 "never contain numeric
    literals for deltas, thresholds" discipline. A simpler, still-valid alternative: a test that
    edits/monkeypatches the config file (or an in-memory override) and asserts the returned grade
    changes accordingly, proving runtime config-sourcing rather than compile-time hardcoding.
  - Where: `tests/unit/rendering/test_grading.py`

- **Config loading fails loud on missing/malformed config, not silently at score time**
  - Category: unit
  - Verifies: a missing required key or non-numeric threshold value in the new config file raises at
    load time (e.g. `KeyError`/`ValueError`), matching SimQ's own `ScoringWeights.load()` fail-loud
    discipline (`INFRA-234`) even though this ticket's loader must not reuse `ScoringWeights` itself.
  - Where: `tests/unit/rendering/test_grading.py`

- **Soft rule non-monotonicity — positive inside healthy band, negative at BOTH extremes**
  - Category: unit
  - Verifies: for at least one real soft rule built on a real metric output (e.g. `ShapeComponent.
    fill_ratio` or `DensityResult.cv`), the delta function returns a positive value for an input
    comfortably inside the configured healthy band, a negative value for an input well below the
    band's low edge, AND a negative value for an input well above the band's high edge — three
    assertions in one test (or three parametrized cases), explicitly proving non-monotonicity (a
    monotonic function could accidentally satisfy "positive somewhere, negative somewhere" without
    being non-monotonic; the test must assert negative at both ends specifically). This is the
    ticket's single most novel piece of math (see investigation.md) and needs the most explicit
    coverage.
  - Where: `tests/unit/rendering/test_grading.py`

- **Hard rule binary-fact shape**
  - Category: unit
  - Verifies: at least one hard rule (e.g. `component_count == 1`) returns a fixed pass-delta on true
    and a fixed fail-delta (or 0/penalty) on false — no gradient, two-value output only.
  - Where: `tests/unit/rendering/test_grading.py`

- **Hard+soft combination step produces one normalized score**
  - Category: unit
  - Verifies: given a fixed set of synthetic hard-rule and soft-rule outputs, the combination function
    returns a single float, and that float changes predictably (monotonically in the *combination*,
    even though individual soft rules are non-monotonic in their own raw input) as individual rule
    deltas are varied — i.e. a strictly larger positive delta set produces a strictly larger combined
    score, holding everything else fixed. This is the "currently-unspecified... design risk" AC calls
    out as this ticket's real design surface.
  - Where: `tests/unit/rendering/test_grading.py`

- **Multi-seed averaging: N=1 identity**
  - Category: unit
  - Verifies: given exactly one per-seed score, the averaging function returns that score unchanged
    (exact float equality, not approximate — this is the ticket's own explicit no-op case).
  - Where: `tests/unit/rendering/test_grading.py`

- **Multi-seed averaging: N>1 arithmetic mean, with synthetic input**
  - Category: unit
  - Verifies: given N>1 synthetic per-seed scores (e.g. `[1.0, 2.0, 3.0]` → `2.0`), the averaging
    function returns the exact arithmetic mean — proves the function genuinely generalizes to N>1
    rather than being hardcoded/special-cased to N=1, per investigation.md's Anti-Drift Hazards. Use
    synthetic float lists, not real corpus data (no real corpus world currently produces N>1 distinct
    per-seed scores through the normal load path — see investigation.md's `wolf_den`/stale-cache
    finding).
  - Where: `tests/unit/rendering/test_grading.py`

- **Module does not subclass PillarScorer or import SimQ's event pipeline**
  - Category: architecture guard (AST-walk, in-file)
  - Verifies: mirrors `test_density.py`/`test_shape.py`'s existing
    `test_<module>_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` pattern —
    walks the new module's AST, asserts no class subclasses `PillarScorer`, asserts no import contains
    `"simulation_quality"` or `"observability.events"`. Directly covers AC #4.
  - Where: `tests/unit/rendering/test_grading.py`

- **Module does not register a new PillarId**
  - Category: architecture guard
  - Verifies: `src/simulation_quality/pillars.py::PillarId` enum member count/members are unchanged
    from their pre-ticket baseline (a simple snapshot-diff or explicit enumerated-members assertion).
    Directly covers AC #4's second clause.
  - Where: `tests/unit/rendering/test_grading.py` or `tests/simulation_quality/test_pillars.py` if such
    a baseline test already exists (confirm at implementation time; not confirmed to exist yet in this
    investigation).

- **Module has zero image/render dependency**
  - Category: architecture guard
  - Verifies: mirrors `test_density.py`/`test_shape.py`'s existing
    `test_<module>_module_has_zero_image_or_render_dependency` pattern (checks for `png_writer`,
    `rendering.render`, `rendering.incremental`, `PIL`, `Pillow` substrings in imports).
  - Where: `tests/unit/rendering/test_grading.py`

- **Does not mutate its inputs**
  - Category: architecture guard
  - Verifies: pass a real `ConnectivityResult`/`DensityResult`/`ShapeComponent` (or the primitives that
    build them) into the grading function(s), assert the same objects are unchanged (identity/equality
    check) after the call — mirrors the "read-only logic did not mutate live state" pattern already
    present in `test_density.py::test_does_not_mutate_authoritative_state` and CLAUDE.md's Architecture
    Rule.
  - Where: `tests/unit/rendering/test_grading.py`

- **Real-corpus end-to-end grading smoke test**
  - Category: integration
  - Verifies: load a real corpus world (e.g. `dungeon_crawl`, matching the sibling modules' own
    real-corpus test convention: `WorldRepository("data/worlds").load_world(...)` →
    `WorldCompiler.compile(spec, seed=42)`), run all four metric modules on the compiled state, feed
    their outputs through this ticket's new grading pipeline end-to-end, and assert a real,
    deterministic S/A/B/C/D/F grade comes out (not a specific grade value pinned as a regression
    anchor unless the planner deliberately wants one — see Anti-Drift Test Guards below for why pinning
    a specific value here is risky before `VISUAL-QUALITY-CALIBRATION` sets real thresholds).
  - Where: `tests/unit/rendering/test_grading.py` (matches sibling convention of colocating real-corpus
    tests in the same `tests/unit/rendering/test_<module>.py` file, not a separate integration
    directory — confirmed by reading `test_density.py`/`test_variants.py`, both of which mix synthetic-
    fixture and real-corpus tests in one file)

## Scoped Pytest Commands

```
python3 -m pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v
python3 -m pytest tests/simulation_quality/test_report.py tests/simulation_quality/test_weights.py tests/simulation_quality/test_grade_regression.py -v
```

Never `pytest tests/`. The first command scopes to the affected `src/rendering/` package plus its
architecture guard; the second scopes to SimQ's own grading/threshold tests, run as a proof of
non-interference (this ticket must not change any SimQ test outcome).

## Anti-Drift Test Guards

- **A test asserting `PillarId`'s member set is byte-identical pre/post this ticket** (see "Module does
  not register a new PillarId" above) directly catches the single most likely accidental architectural
  violation: an implementer reaching for the existing SimQ enum instead of building the independent
  vocabulary this ticket requires.
- **The non-monotonicity test's three-point assertion (healthy-band positive, both-extremes negative)**
  guards against the most likely silent scope-creep failure mode: an implementer building a soft rule
  that is actually monotonic (e.g. "higher is always better, capped") because that is the far more
  common/familiar shape (it's exactly what every one of SimQ's own rules does) — a test that only
  checks "positive somewhere, negative somewhere" would not catch this; the test must explicitly assert
  negative at the *high* extreme, not just the low one.
- **The N>1 multi-seed averaging test with synthetic (not real-corpus) input** guards against the
  averaging function silently degrading into an N=1-only implementation that happens to pass today's
  only real-corpus case — a real risk given investigation.md's finding that no real corpus world
  currently produces N>1 distinct scores through the normal load path, which could tempt an
  implementer into skipping genuine N>1 support as "unreachable in practice."
- **Explicitly do NOT add this system to any CI-gating/regression-baseline script** — a test (or a
  grep-based check) confirming the new module/config is absent from whatever gate-check manifest this
  repo uses for report-only-vs-CI-gated distinctions would catch an accidental over-eager wiring, though
  this is lower-priority than the tests above since the ticket's Out of Scope is unambiguous and no
  existing gate script currently references `src/rendering/` at all (confirmed: none of the four
  shipped siblings needed such a guard).
- **Do not pin a specific numeric grade for the real-corpus smoke test as a hard regression anchor**
  unless deliberately choosing to — the exact healthy-band boundary numbers are explicitly
  uncalibrated at this ticket's stage (`TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s scope, not this
  ticket's), so a tightly-pinned grade value here would make that later calibration ticket's own,
  intended threshold changes look like a false regression in this ticket's tests. Assert grade is one
  of the six valid letters and/or that the combined score is a finite float, not a specific letter,
  unless the planner deliberately wants a looser regression anchor with documented tolerance (mirroring
  `test_grade_regression.py`'s `_within_band`/tolerance pattern from SimQ's own suite).
