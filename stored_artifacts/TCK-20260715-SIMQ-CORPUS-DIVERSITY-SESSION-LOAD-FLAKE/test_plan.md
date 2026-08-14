---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE
artifact_type: test_plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Test Plan — TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE

## Regression Surface

Existing tests that must keep passing after either remedy is implemented. Grouped by
category; commands are scoped, not repo-wide, per project Testing Rule.

**Unit — `test_grade_regression.py` (the file remedy (a) would touch):**
- `tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid`
- `tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression`
- `tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged`
  — hard anti-drift guard on `_within_band`'s default; must not be touched or broken by
  an `_within_score_tolerance` override table.
- `tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged`
  — 76-entry count guard; remedy (a) must not add/remove any `grade_anchors.json` key.
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[*]`
  (all `FAST_ANCHOR_KEYS`, parametrized) — every anchor **other than** the 3 named ones
  must see byte-identical pass/fail behavior before and after remedy (a); this is the
  primary regression risk of a scoped override.
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[*]`
  (all `SLOW_ANCHOR_KEYS`, parametrized, `-m slow`) — same non-regression requirement for
  the slow-tier anchors.
- `tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor`
- `tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor`
- `tests/simulation_quality/test_grade_regression.py::test_information_intent_execution_fires_through_kernel_tick_once`
  — unrelated to this ticket's scope but lives in the same file; must not regress from an
  edit to shared imports/constants.

**Unit — `test_corpus_diversity.py` (the file remedy (b) would touch the *invocation
shape* of, not the content):**
- `tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_500t_cognition_bit_identical_under_load`
  — pre-existing bit-identical precedent guard; must not be modified (Out of Scope).
- `tests/unit/worldassembly/test_corpus_diversity.py::test_generated_frontier_3_42_extended_population_stability`
  — pre-existing tolerance precedent guard; must not be modified (Out of Scope).
- All 14 `*_grade_stability` guards added by `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`
  (`-k "grade_stability"`) — must remain green; remedy (a) reuses their `abs_floor`
  values as reference data (read-only), remedy (b) changes only *how* the file is
  invoked in CI, not any guard's assertions.
- Non-`slow`-marked tests in the same file (`test_entity_count_band`,
  `test_population_stability`, `test_hazard_kind_completeness`,
  `test_hazard_kind_matches_populating_faction_immunity`,
  `test_module_family_anchored`) — unaffected by either remedy but share the file; a
  scoping error in Implement (e.g. accidentally filtering these out of a restructured CI
  step) would be a silent regression.

**Integration / CI structure:**
- `.github/workflows/test.yml`'s `slow` job as a whole — whichever remedy is adopted,
  the job's dependency graph (`needs: [...]`), `if:` condition
  (`github.ref == 'refs/heads/main' || github.base_ref == 'main'`), and the subsequent
  `Legacy regression`/`Upload certification report` steps must be preserved unless the
  ticket's own AC #3 explicitly changes them.

## New Tests Required

Per the ticket's Acceptance Criteria — one entry per criterion that produces a new test
artifact. (AC #1, the remedy-selection determination itself, is documented in the
ticket's Implementation Notes, not a test.)

1. **`test_within_band_default_tolerance_unchanged`-equivalent protection for remedy (a)**
   (AC #2, if remedy (a) is adopted)
   - Test name: `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` (or
     equivalent)
   - Category: unit / anti-drift guard
   - What it verifies: for every `run_key` in `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`
     **except** the override table's keys, `_within_score_tolerance(actual, anchor)`
     called with no override kwargs produces the identical pass/fail result as calling it
     with whatever override-lookup helper the implementation adds (i.e., the lookup falls
     through to the global defaults for every other anchor, verified programmatically —
     not just by inspection). Directly analogous in spirit to
     `test_within_band_default_tolerance_unchanged`, but for the new override mechanism
     rather than `_within_band`'s single default.
   - Where it lives: `tests/simulation_quality/test_grade_regression.py`, adjacent to
     `test_within_band_default_tolerance_unchanged` and
     `test_score_tolerance_catches_within_band_regression`.

2. **Override-table correctness for the 3 named pillars** (AC #2, if remedy (a) is
   adopted)
   - Test name: `test_score_tolerance_override_widens_only_named_pillars` (or per
     implementation's chosen structure — may be folded into test 1 above as parametrized
     cases)
   - Category: unit
   - What it verifies: the override table contains exactly the 3 named
     `(run_key, pillar)` entries (`urban_political_seed123_1000t`/SOCIAL,
     `urban_political_seed123_1000t`/ECONOMY, `frontier_marches_seed42_200t`/NARRATIVE)
     — no more, no fewer — and that each override's `abs_floor`/`rel_pct` value is wider
     (not narrower) than the global default for that anchor's committed score, so the
     override can only ever loosen, never silently tighten, the check for these 3.
   - Where it lives: `tests/simulation_quality/test_grade_regression.py`.

3. **Controlled comparison run result** (AC #3, if remedy (b) is adopted)
   - Test name: not a pytest test — a recorded artifact per the ticket's own AC #3
     wording ("at least one controlled comparison run ... and its result recorded"). If
     remedy (b) is the subprocess-splitting approach, this is most naturally captured as
     a CI workflow change plus a working-log/staging-artifact record (e.g.
     `staging_artifacts/.../isolation_comparison.md`) rather than a new pytest test —
     flag this distinction for the Plan phase since "New Tests Required" is not quite the
     right bucket for this AC.
   - Category: integration / CI-process (not a pytest unit test)
   - What it verifies: whether running the 32-test `-m slow` file split into N isolated
     subprocess invocations (or `pytest-xdist`-parallelized, if that path is chosen
     instead) measurably reduces or eliminates the cumulative-load-driven flake, compared
     to at least one more sequential full-file baseline run for contrast.
   - Where it lives: `.github/workflows/test.yml` (the mechanism change) +
     `staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/` (the
     recorded comparison, analogous to `repro_sweep.md`'s precedent).

4. **Architecture guard: CI `slow` job still covers all 32 `-m slow`/`-m extra_slow`
   corpus-diversity tests after any invocation-shape change** (AC #3, if remedy (b) is
   adopted)
   - Test name: `test_slow_ci_job_still_covers_full_corpus_diversity_file` (or a
     `tests/architecture`/`tests/ci`-scoped static check, matching repo convention for
     CI-shape guards if one exists — verify at Implement time)
   - Category: architecture guard
   - What it verifies: whatever restructuring of the `slow` CI step occurs (splitting
     into N subprocess calls, or adding `-n`/`--dist`), the union of tests actually
     executed across all resulting invocations still equals the full
     `-m "slow or extra_slow"` selection — no test silently dropped by a scoping mistake
     during the CI restructuring (this is the concrete anti-drift risk of remedy (b)).
   - Where it lives: a static/architecture-tier test, or (if no such CI-shape-checking
     test category exists yet in this repo) a documented manual verification step in the
     ticket's Implementation Notes — confirm which applies at Implement time by checking
     `tests/architecture/`, `tests/static/` for any existing CI-workflow-parsing
     precedent before deciding to add a new one.

5. **If neither remedy is adopted** (AC #5)
   - No new test required — the AC requires documentation (ticket Implementation Notes +
     parity ledger update), not a test artifact. Do not force a test into existence to
     satisfy this AC if the determination is "neither."

## Scoped Pytest Commands

Regression verification, scoped to the domain under modification — never
`pytest tests/` unscoped.

```bash
# test_grade_regression.py — fast tier (default marker filter excludes slow)
pytest tests/simulation_quality/test_grade_regression.py -v

# test_grade_regression.py — slow tier explicitly (SLOW_ANCHOR_KEYS + any new override tests)
pytest tests/simulation_quality/test_grade_regression.py -m slow --resource-budget large -v

# corpus_diversity.py — the 16 pre-existing/precedent grade_stability-adjacent guards,
# not the full 32-test slow file, for fast iteration during Implement
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "grade_stability" -m slow --resource-budget large -v

# corpus_diversity.py — full 32-test file, the literal AC #4-equivalent regression gate
# both this ticket and its parent close on; required at least once at Verify time,
# and again as part of any remedy (b) controlled-comparison run
pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v

# Sanity check that INFRA-271's underlying fix path remains green (adjacent parity entry)
pytest tests/simulation_quality/test_weights.py -v
```

If remedy (b) restructures the CI invocation (subprocess-splitting or `xdist`), the
"controlled comparison run" itself is not a single scoped command but the ticket's own
before/after pair — run the full sequential baseline (command above) at least once more
immediately before and after the restructuring change to isolate whether the change
itself affected the flake rate, not just wall-clock timing drift between sessions.

## Anti-Drift Test Guards

- **`test_within_band_default_tolerance_unchanged`** (existing,
  `test_grade_regression.py:547-553`) — already catches a global `_within_band` default
  widening; remains the negative-control guard proving remedy (a) did not touch
  `_within_band` at all (only `_within_score_tolerance`'s call sites for the 2 anchor
  tests).
- **New test 1 above** (`test_score_tolerance_overrides_do_not_affect_unlisted_anchors`)
  is itself the primary anti-drift guard for remedy (a) — it exists specifically to catch
  the failure mode where an override-lookup helper is implemented sloppily (e.g., a bug
  that widens tolerance for all anchors instead of just the 3 named ones, or a `.get()`
  default that silently changes behavior for a fourth anchor).
- **`test_grade_anchors_entry_count_unchanged`** (existing) — catches a remedy (a)
  implementation that accidentally adds/removes a `grade_anchors.json` key while wiring
  in override lookups (should not happen if the override table lives in
  `test_grade_regression.py` as a separate constant, but this guard exists as a backstop).
- **New architecture-guard test 4 above** — the primary anti-drift guard for remedy (b);
  a CI restructuring that silently drops test coverage (e.g., a subprocess-splitting loop
  that misses one of the 32 tests due to an off-by-one in a `-k` filter list) is a much
  worse outcome than the flake it was meant to fix, and would not be caught by any
  existing test since it manifests only in CI's actual invocation shape, not in a local
  `pytest` run against the file directly.
- **Full-file sequential re-run of `test_corpus_diversity.py -m slow`** (existing
  command, not a new test) — must still be run at least once post-remedy regardless of
  which remedy is chosen, to confirm the specific 2-anchor flake pattern observed in the
  parent ticket's Step 14 does not reproduce under whatever new invocation shape (for
  remedy (b)) or whatever new tolerance width (for remedy (a), where a wider tolerance
  should make the specific single-draw failure mode structurally impossible for the 3
  named pillars, independent of CI invocation shape).
- **Parity ledger `test_path` validity** — whichever of INFRA-272/INFRA-273 is updated or
  extended, its cited `test_path` must be re-run and confirmed green as part of Verify,
  not just edited in the YAML (matching the project's parity-ledger discipline that P0/P1
  entries require a passing `test_path`; these are P1/P2 but the same discipline applies
  per the Authoritative Mechanics Rule).
