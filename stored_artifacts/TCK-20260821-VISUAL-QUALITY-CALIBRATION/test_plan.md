---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-CALIBRATION
artifact_type: test_plan
tags: [visualization, simulation-quality, calibration, world]
---

# Test Plan — TCK-20260821-VISUAL-QUALITY-CALIBRATION

## What is and isn't testable here (read first)

This ticket is a `tools/` **calibration script**, not a `src/rendering/` library module — the same
shape as `tools/calibrate_simq.py`, whose own test file
(`tests/simulation_quality/test_calibrate_simq.py`) tests **the script's own logic and guard
behavior**, never the calibrated numeric values it produces. This test plan follows that exact
precedent, not the seven prior siblings' `src/rendering/`-module pytest shape:

- **Testable, and required**: CLI argument parsing/plumbing, output-artifact file shape and atomic
  write behavior, the run-integrity guard's actual raise/pass behavior (via forced-failure
  injection, mirroring `test_calibrate_simq.py`'s `_force_small_queue`/monkeypatch pattern), the
  "Shape (and Variants' TVD) zero-cross-seed-variance is recorded, not treated as a failure" logic,
  config-header provenance-field presence, and the stdlib-only/no-`simulation_quality`-coupling
  architectural guards.
- **Not testable here, and must not be asserted against**: the actual calibrated numeric healthy-
  band values (e.g. "density `cv`'s healthy band is `[0.5, 0.9]`") — these are empirical outputs of
  running real worlds, not a regression anchor. No test in this plan pins a specific calibrated
  number. (Contrast with the four shipped metric-family test suites, which correctly *do* pin
  specific numbers like `dungeon_crawl`'s `cv == 0.678` — those are parity anchors for
  **already-shipped, already-verified formulas**; this ticket produces **new, first-time-computed**
  threshold data that has no existing "correct" value to regress against.)

## Regression Surface

Existing tests that must keep passing — this ticket adds a new script and, if the planner chooses
option (a) from investigation.md's Risks (a separate calibration-report file), touches no existing
production file at all. If option (b) is chosen (directly rewriting `config/rendering/
grade_thresholds.toml`), the regression surface below becomes load-bearing for real, not just
defensive.

**Unit — `src/rendering/` metric families and grading (must not regress, since this ticket reads
their real outputs but must not modify their code):**
- `tests/unit/rendering/test_connectivity.py`
- `tests/unit/rendering/test_density.py`
- `tests/unit/rendering/test_shape.py`
- `tests/unit/rendering/test_variants.py`
- `tests/unit/rendering/test_grading.py`
- `tests/architecture/test_rendering_zero_new_dependency_guard.py` (package-wide stdlib-only guard
  over `src/rendering/*.py` — this ticket's script lives in `tools/`, outside this guard's scope,
  but must not cause it to start failing by, e.g., accidentally adding an import to a `src/
  rendering/` file as a side effect of wiring the calibration script in)

**Unit/integration — `tools/calibrate_simq.py` (the cited precedent; must not regress, since this
ticket only reads it as a reference pattern, never imports from or edits it):**
- `tests/simulation_quality/test_calibrate_simq.py`
- `tests/simulation_quality/test_calibrate_world_loading.py`

**Integration — world loading/compilation (this ticket's script is a new, real consumer of this
path; must not regress):**
- `tests/unit/worldbuilding/` (or wherever `WorldRepository`/`WorldCompiler` are covered — confirm
  exact path at implementation time; not read in full this session, out of this investigation's
  direct scope, but the calibration script's own tests below exercise the same real path directly)

**If option (b) is chosen (direct rewrite of `config/rendering/grade_thresholds.toml`):**
- `tests/unit/rendering/test_grading.py::test_config_loads_from_real_default_path` (or equivalent —
  confirm exact test name at implementation time) must still pass against the post-calibration file,
  proving the rewritten TOML is still valid, structurally-complete `GradeConfig` input.

## New Tests Required

Per acceptance criteria, one entry per required new test. File path assumes
`tools/calibrate_rendering.py` per investigation.md's recommendation; adjust if the planner names it
differently.

1. **`test_cli_runs_all_four_families_for_one_world_seed_pair`**
   Category: integration (real `WorldRepository`/`WorldCompiler`, no mocking of compile itself).
   Verifies: invoking the script's main entrypoint (or its internal per-(world,seed) runner
   function directly, mirroring `test_calibrate_world_loading.py`'s pattern of testing
   `_load_world_state` directly rather than only via subprocess/CLI) for one real world (e.g.
   `dungeon_crawl`) and one seed produces a JSON artifact containing all four families' raw
   structured outputs (connectivity, density, shape, variants/TVD) with no exception raised on a
   clean run.
   Location: `tests/tools/test_calibrate_rendering.py`

2. **`test_output_artifact_written_to_correct_location_atomically`**
   Category: unit/integration.
   Verifies: the per-(world, seed) output artifact lands at the documented location (mirroring
   `calibrate_simq.py`'s `data/calibration/{name}_seed{seed}_{ticks}t/` convention, or this ticket's
   own equivalent — confirm exact naming in plan.md) via a tmp-write-then-`os.rename()` atomic
   pattern (assert no `.tmp` file is left behind after a successful run; matches
   `QualityPersistence.write_report`/`write_run_health`'s established pattern this ticket should
   mirror).
   Location: `tests/tools/test_calibrate_rendering.py`

3. **`test_seed_flag_is_singular_per_invocation`**
   Category: unit (CLI argument parsing).
   Verifies: the script's `--seed` argument accepts exactly one integer per invocation (mirroring
   `calibrate_simq.py`'s own CLI shape, per investigation.md point 1) — multi-seed sweeping is
   achieved by the calling convention (a shell/Python loop over multiple invocations), not a single
   invocation accepting a seed list. Guards against silent scope drift toward a different CLI shape
   than the ticket's own Assumptions section specifies ("one seed per invocation").
   Location: `tests/tools/test_calibrate_rendering.py`

4. **`test_calibration_run_integrity_guard_fails_loud_on_corrupted_compile`**
   Category: unit (forced-failure injection, mirroring `test_calibrate_simq.py`'s
   `_force_small_queue`/monkeypatch approach).
   Verifies: AC #5's run-integrity guard actually raises (an equivalent
   `CalibrationIntegrityError`-style exception, this ticket's own class) rather than silently
   writing a data point, when the compile/run it wraps is corrupted. The exact injection mechanism
   depends on which guard design the planner picks (see investigation.md's Risks):
   - If the guard checks `compile_report["warnings"]`/`entity_count`/`region_count`: construct or
     monkeypatch a `WorldCompiler.compile()` call to return a report with a non-empty `warnings`
     list (or `entity_count == 0`) and assert the guard raises.
   - If the guard reuses `calibrate_simq.py`'s literal queue-drop/SURVIVAL-mode check (relevant only
     if trail-activity calibration, which ticks a real `Kernel`, is in scope): adapt
     `test_calibrate_simq.py::TestQueueOverflowGuard`'s `_force_small_queue` pattern directly against
     this script's own `Kernel`-driving code path.
   This test's exact shape is contingent on the plan's guard design — flagged here as a required
   test *category*, with the concrete mechanism to be finalized once plan.md resolves the open
   question investigation.md raises.
   Location: `tests/tools/test_calibrate_rendering.py`

5. **`test_calibration_run_succeeds_normally_on_clean_compile`**
   Category: unit (positive-path counterpart to #4).
   Verifies: a normal, uncorrupted run does **not** raise the integrity guard and does produce a
   complete output artifact — guards against an overly aggressive guard that false-positives on
   healthy runs (the same "succeeds normally with zero drops" counterpart
   `test_calibrate_simq.py::TestQueueOverflowGuard::test_calibrate_simq_succeeds_normally_with_zero_drops`
   already establishes as required alongside its failure-path sibling).
   Location: `tests/tools/test_calibrate_rendering.py`

6. **`test_shape_zero_cross_seed_variance_is_recorded_as_expected_not_flagged`**
   Category: unit/integration (real corpus, `dungeon_crawl` — the durable, structural
   seed-invariance anchor per `VARIANTS-METRIC`'s own finding, **not** `sandbox_world`, whose
   invariance is a cache-staleness artifact — see investigation.md point 5).
   Verifies: running Shape's `connected_components` across >=2 distinct seeds for the same real
   world produces an output artifact that explicitly notes/records the resulting zero variance as
   expected (whatever field/flag the plan designs for this — e.g. a `"seed_variance": "none
   (expected)"` marker or similar), and critically, that this zero-variance condition does **not**
   trip the run-integrity guard from test 4 (a guard that treats "identical across seeds" as
   itself suspicious would be a real, silent bug this test exists to catch).
   Location: `tests/tools/test_calibrate_rendering.py`

7. **`test_density_and_connectivity_show_real_cross_seed_variance_in_output`**
   Category: integration (real corpus).
   Verifies: unlike test 6, Density's `cv` (confirmed empirically in investigation.md point 5 to
   vary meaningfully across seeds — `sandbox_world`: 0.6478 at seed 42 vs 0.9105 at seed 137) and
   Connectivity's `blocked_tiles`-dependent inputs genuinely differ across seeds in the calibration
   output for at least one real world — a sanity check that the calibration sweep is actually
   capturing real variance where it exists, not accidentally collapsing everything to a single
   value (which would silently defeat the entire multi-seed calibration purpose).
   Location: `tests/tools/test_calibrate_rendering.py`

8. **`test_output_config_header_matches_grade_thresholds_yaml_field_set`**
   Category: unit.
   Verifies: AC #2's provenance header (date, ticket ID, world(s), seeds, ticks) is present in the
   written config/report output, structurally matching `config/simulation_quality/
   grade_thresholds.yaml`'s field set (`Calibration: <date> | <ticket_id>`, a
   scope-of-run metadata line pluralized correctly for multi-world coverage per investigation.md
   point 2, an observed-values block, a validation-summary line) — parse the header comment lines
   and assert each required field is present, not a byte-for-byte string match (the field set is
   what AC #2 requires matched, not the exact single-world wording of the precedent).
   Location: `tests/tools/test_calibrate_rendering.py`

9. **`test_no_pytest_or_ci_gate_asserts_against_calibrated_threshold_values`**
   Category: architecture guard (repo-wide grep/AST check, mirroring the spirit of
   `tests/architecture/test_rendering_zero_new_dependency_guard.py`'s static-check approach).
   Verifies: no test file anywhere in `tests/` imports this ticket's calibration output config and
   asserts a specific numeric value from it (grep for the new config file's path across `tests/`,
   assert zero hits outside this ticket's own script-logic tests, or a stronger AST-based check if
   the plan prefers). Directly enforces Out of Scope's "No pytest/CI gate consumes these
   thresholds" as a checkable invariant, not just a code-review convention.
   Location: `tests/architecture/test_calibration_output_not_ci_gated.py` (new file, architecture
   category — matches the existing `tests/architecture/` convention for repo-wide static
   invariants like the stdlib-only guard) — or folded into `tests/tools/test_calibrate_rendering.py`
   if the planner judges a dedicated architecture-tier file disproportionate for one check; either
   placement satisfies the requirement, folding is the lighter-weight default absent a reason for a
   dedicated file.

10. **`test_calibration_script_module_does_not_import_simulation_quality_or_observability_events`**
    Category: architecture guard (AST-walk, mirroring `test_density.py`'s/`test_shape.py`'s
    per-module `test_<module>_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`
    pattern, adapted to a `tools/` script rather than a `src/rendering/` module).
    Verifies: the calibration script's own source file contains no `import` statement whose name
    contains `"simulation_quality"` or `"observability.events"` — enforces the independence
    boundary the dispatching instructions and investigation.md both confirm is required, the same
    way the four shipped metric-family modules already enforce it for themselves.
    Location: `tests/tools/test_calibrate_rendering.py`

11. **`test_calibration_run_does_not_mutate_any_resolved_world_cache_on_disk`**
    Category: architecture guard / integration.
    Verifies: running the calibration script against a real world does not write to or modify any
    file under `data/worlds/{world}/resolved/` — directly enforces investigation.md's Anti-Drift
    Hazard against silently "fixing" stale `resolved/world.resolved.yaml` caches as a side effect
    (record `os.path.getmtime`/file hash of the relevant `resolved/` files before and after the run,
    assert unchanged).
    Location: `tests/tools/test_calibrate_rendering.py`

## Scoped Pytest Commands

```
# This ticket's own new tests
pytest tests/tools/test_calibrate_rendering.py -m "not slow and not extra_slow" --tb=short -q

# If a dedicated architecture-tier file is used for test 9
pytest tests/architecture/test_calibration_output_not_ci_gated.py -m "not slow and not extra_slow" --tb=short -q

# Regression surface: the four metric families + grading + their stdlib-only guard (read, not modified, by this ticket)
pytest tests/unit/rendering -m "not slow and not extra_slow" --tb=short -q

# Regression surface: calibrate_simq.py itself (read as reference pattern, never imported/edited)
pytest tests/simulation_quality/test_calibrate_simq.py tests/simulation_quality/test_calibrate_world_loading.py -m "not slow and not extra_slow" --tb=short -q

# Package-wide architecture guards (must stay green — this ticket's script lives outside their scope but must not break them)
pytest tests/architecture -m "not slow and not extra_slow" --tb=short -q
```

Never `pytest tests/` — scoped per CLAUDE.md's Testing Rule to the domains this ticket actually
touches (`tools/`, `tests/tools/`, and the `src/rendering/`/`tests/simulation_quality/` surfaces it
reads from without modifying).

## Anti-Drift Test Guards

- **Test 9** is the direct enforcement of Out of Scope's CI-gating prohibition — without it, a
  future session could add a threshold-consuming assertion without any static check catching the
  scope violation until a human review happens to notice.
- **Test 10** is the direct enforcement of the SimQ-independence boundary — without it, a future
  edit could import `src.simulation_quality` for convenience (e.g. to reuse a config-loading
  helper) without any test catching the architectural drift, exactly the failure mode the four
  shipped metric modules' own AST-walk guards already exist to prevent for themselves.
- **Test 11** is the direct enforcement of the "do not silently fix the stale resolved-cache" Anti-
  Drift Hazard `VARIANTS-METRIC` already established and this ticket inherits — without it, a
  future implementer chasing "real" seed-varying terrain for a richer calibration sample could
  regenerate a `resolved/world.resolved.yaml` cache as a quick fix, silently mutating durable
  world-compilation state (with downstream certification-corpus golden-hash implications) as a side
  effect of what should be a read-only calibration run.
- **Test 6** is the direct enforcement of AC #3 as a checkable invariant, not just a documentation
  claim — without it, a future change to the guard logic (test 4) could start treating Shape's (or
  Variants' TVD) legitimate zero-variance as a run failure, silently breaking calibration for those
  two families every time it runs.
- **Test 3** guards against silent CLI-shape drift away from the ticket's own explicit Assumptions
  ("one seed per invocation") toward, e.g., an `nargs="+"` list-of-seeds design that would change
  the calling convention documented in this ticket's own scope without anyone deciding that
  deliberately.
