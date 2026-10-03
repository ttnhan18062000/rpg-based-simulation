---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP
artifact_type: test_plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Test Plan — TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP

## Regression Surface

Existing tests that must keep passing after this ticket's `SCORE_TOLERANCE_OVERRIDES` table
edit (adding COGNITION and SOCIAL entries for `urban_political_seed123_1000t`, on top of the 3
existing entries which must remain byte-identical).

### Unit / structural (`tests/simulation_quality/test_grade_regression.py`)

- `test_grade_anchor_file_exists_and_valid` — must still pass; unaffected by the override table
  (validates `grade_anchors.json` structure only). Note: this test has a known pre-existing
  local-data dependency on `hero_guild_routing_seed42_1000t` calibration data being present —
  confirmed by the parent ticket (`TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`'s
  Deviations section) to fail identically on unmodified pre-ticket code when that data is
  absent; not a regression this ticket introduces.
- `test_score_tolerance_catches_within_band_regression` — synthetic before/after proof,
  independent of the override table's contents.
- `test_within_band_default_tolerance_unchanged` — asserts `_within_band.__defaults__ == (1,)`;
  independent of the override table.
- `test_grade_anchors_entry_count_unchanged` — asserts 76 scenario entries; this ticket does
  not touch `grade_anchors.json`, so this must still pass unmodified.
- `test_grade_within_anchor_band` (fast, `-k "test_grade_within_anchor_band and not long_run"`)
  — the full `FAST_ANCHOR_KEYS` parametrized sweep; `urban_political_seed123_1000t` is not in
  this list (it is a `SLOW_ANCHOR_KEYS` entry), so no fast-tier case exercises this ticket's
  edited table entries directly, but every other run_key's cases must remain unaffected
  (regression surface for `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`
  below already covers this more precisely).
- `test_grade_within_anchor_band_long_run` (slow, all `SLOW_ANCHOR_KEYS` other than
  `urban_political_seed123_1000t`) — must remain pass/skip as before (this ticket's table edit
  only affects the `urban_political_seed123_1000t` key's kwargs; every other slow key falls
  through to defaults exactly as before).

### `tests/unit/worldassembly/test_corpus_diversity.py` — precedent guards (NOT to be edited)

- `test_urban_political_seed123_1000t_social_economy_grade_stability` — the anchor's only
  existing `grade_stability` guard (SOCIAL `abs_floor=2.9568`, ECONOMY `abs_floor=0.2878`).
  Must remain byte-identical and passing; this ticket's SOCIAL `SCORE_TOLERANCE_OVERRIDES`
  entry (a different mechanism — single-draw floor, not 3-trial-mean floor) does not touch this
  guard's own constants.
- All other 13 `grade_stability` guards — untouched, must remain green (or the same
  known-flaky-under-sustained-session-load caveat documented in
  `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` Section 8,
  not a new regression).

### `tests/simulation_quality/test_weights.py`

- `test_real_config_seven_known_collisions_resolve_per_pillar` — unrelated to the tolerance
  table; included because `INFRA-272`'s existing `test_path` cites it as part of this anchor's
  overall regression surface. Must remain passing, unmodified.

## New Tests Required

Per acceptance criteria:

1. **Override-table edit verified structurally.**
   - Test: `test_score_tolerance_override_table_scoped_to_named_pillars` (existing test,
     **modified**, not new) — its hard-coded `set(SCORE_TOLERANCE_OVERRIDES.keys()) == {...}`
     assertion must be updated to the final entry set this ticket lands (at minimum the 3
     existing entries; plus COGNITION and/or SOCIAL per the planner's resolution of
     investigation.md's Risk #1). No new test function needed — this existing anti-drift guard
     already asserts both the exact key set and the widen-only invariant
     (`abs_floor > default_width`) for every entry, generically, with no per-entry code
     required.
   - Category: architecture guard (anti-drift).
   - Verifies: the table contains exactly the evidence-derived entries, no more, no less; every
     entry genuinely widens tolerance relative to that anchor's committed score.
   - Location: `tests/simulation_quality/test_grade_regression.py` (existing function, edited).

2. **Long-run parametrized case passes against fresh real data (AC-mandated proof).**
   - Test: `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` (existing
     parametrized case, no code change — exercised against regenerated calibration data).
   - Category: integration (real calibration data, real Kernel, no `audit_mode`).
   - Verifies: with the new override(s) wired in, a real fresh calibration draw at the default
     `data/calibration/urban_political_seed123_1000t/` path passes both the band check and the
     score-tolerance check for all 10 pillars.
   - Location: `tests/simulation_quality/test_grade_regression.py` (existing, run not edited).
   - **Precondition**: `data/calibration/urban_political_seed123_1000t/quality_report.json`
     must exist (regenerate via `.venv/bin/python3 tools/calibrate_simq.py --name
     urban_political --seed 123 --ticks 1000`, no custom `--output`, so the parametrized test
     finds it at the default path instead of skipping).
   - **Known residual risk (not a new gap, documented precedent)**: because COGNITION's refire
     mechanism showed a 25% (2/8) spike rate this session, there is a real, non-trivial chance
     a single regenerated draw for this AC-mandated run lands in the spike case. If the
     implementer's own regenerated draw shows a COGNITION spike **and** Risk #1 was resolved as
     option (a) (override applied with `abs_floor=2.0435`), the test should still pass (the
     floor was derived to cover exactly this case). If it fails anyway, re-run once before
     escalating — consistent with every prior ticket in this chain's documented single-draw
     variance handling — and record the outcome in Implementation Notes either way.

3. **No regression to unlisted `(run_key, pillar)` pairs.**
   - Test: `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` (existing, self-
     adjusting, no edit needed) — already dynamically skips whatever is in the table.
   - Category: architecture guard (anti-drift).
   - Verifies: every `(run_key, pillar)` pair not in the (now possibly 4- or 5-entry) table
     still falls through to the global default kwargs, byte-identical to calling
     `_within_score_tolerance` with no overrides.
   - Location: `tests/simulation_quality/test_grade_regression.py` (existing, unmodified).

4. **No new `grade_stability` guard** — per the ticket's Out of Scope and this investigation's
   Risk #1/#2 findings, no new dedicated 3-trial-mean guard is added unless the planner
   explicitly resolves Risk #1 as option (b) (COGNITION needs a different remedy shape). If (b)
   is chosen, a new guard function (e.g.
   `test_urban_political_seed123_1000t_cognition_grade_stability`) would be required, following
   the exact pattern of `test_urban_political_seed123_1000t_social_economy_grade_stability`
   (3 fresh same-seed trials, mean-based floor) — flagged here as conditional scope, not
   committed to by this test plan.

## Scoped Pytest Commands

Never run `pytest tests/` (project Testing Rule). All commands scoped to the affected files:

```bash
# Fast, no-calibration-data-needed structural/anti-drift surface
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k "test_grade_within_anchor_band and not long_run" -v

# Regenerate real calibration data at the default path (prerequisite for the slow case below)
.venv/bin/python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000

# AC-mandated slow proof against fresh real data
.venv/bin/python3 -m pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v

# Precedent guard — confirm untouched and still passing
.venv/bin/python3 -m pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" -m slow --resource-budget large -v

# git diff scope check (per AC)
git diff --stat -- src/engine/kernel.py tests/unit/worldassembly/test_corpus_diversity.py tests/simulation_quality/fixtures/grade_anchors.json
```

Post-verification cleanup (per environment note, `data/calibration/` is not covered by the
standard workflow's automated cleanup):

```bash
rm -rf data/calibration/* data/runs/* reports/release_proof/*
```

## Anti-Drift Test Guards

- **`test_score_tolerance_override_table_scoped_to_named_pillars`'s exact-set assertion** is
  itself the primary anti-drift guard for this ticket's own scope — it will fail loudly if the
  implementer adds an entry this investigation did not recommend, forgets to add one that was
  recommended, or accidentally touches an existing entry's value (the widen-only invariant
  check catches an accidental narrowing).
- **`test_score_tolerance_overrides_do_not_affect_unlisted_anchors`** catches any accidental
  cross-contamination — e.g. if an implementer typo'd a different `run_key` (such as
  `urban_political_seed42_1000t` instead of `_seed123_`) while adding the new entries, this
  test would catch the unlisted-anchor's kwargs unexpectedly changing.
- **`git diff --stat -- src/engine/kernel.py tests/unit/worldassembly/test_corpus_diversity.py
  tests/simulation_quality/fixtures/grade_anchors.json`** (AC-mandated) — must show no output
  for `kernel.py` and `test_corpus_diversity.py` (byte-identical); `grade_anchors.json` must
  show no diff unless the planner explicitly justifies re-centering with cited evidence (this
  investigation's recommendation is to re-center neither SOCIAL nor COGNITION's anchor — see
  investigation.md Anti-Drift Hazards).
- **`test_grade_anchors_entry_count_unchanged`** (existing, run as part of the fast surface) —
  catches an accidental scenario-key add/drop in `grade_anchors.json`, which this ticket must
  not touch.
- **Manual read-diff on `docs/parity_ledger/infrastructure.yaml`** — `INFRA-272` (and, per this
  investigation's recommendation, `INFRA-273`) must only receive appended text, never edited
  in-place. Verify via `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/
  infrastructure.yaml'))"` (parses cleanly) plus a manual diff review confirming only additions.
- **COGNITION-specific guard (conditional on Risk #1's resolution)**: if option (a) is chosen
  (plain override), no additional guard is needed beyond the existing anti-drift tests above —
  but Implementation Notes must explicitly record the caveat from investigation.md Risk #1 (the
  floor's width relative to the anchor) so a future reader does not mistake a wide floor for an
  oversight. If option (b) is chosen (new guard), that guard's own 3-trial-mean assertion
  becomes an additional anti-drift check that COGNITION's *typical* behavior (not just its
  worst single-draw case) stays centered near the anchor.
