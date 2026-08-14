---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE
artifact_type: test_plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Test Plan — TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE

## Regression Surface

Existing tests that must keep passing, unmodified in behavior except where explicitly named
as needing an update (the 2 anti-drift guards below).

### Unit — `tests/simulation_quality/test_grade_regression.py`

- `test_grade_anchor_file_exists_and_valid` — must stay green; `grade_anchors.json` is not
  touched by this ticket's recommended fix.
- `test_grade_anchors_entry_count_unchanged` — must stay green (76 scenario entries); no
  anchor added/removed/duplicated.
- `test_within_band_default_tolerance_unchanged` — must stay green; `_within_band`'s default
  (`(1,)`) is untouched.
- `test_score_tolerance_catches_within_band_regression` — must stay green; the synthetic
  before/after proof does not use the override table (calls `_within_score_tolerance` with no
  `run_key`/`pillar`), so it is unaffected by adding a 3rd table entry.
- `test_grade_within_anchor_band` (all `FAST_ANCHOR_KEYS` parametrizations) — must stay green;
  none of the fast keys are `urban_political_seed123_1000t` (that key is slow-tier only), so
  this parametrized test is structurally unaffected by the new entry.
- `test_grade_within_anchor_band_long_run` (all `SLOW_ANCHOR_KEYS` parametrizations **other
  than** `urban_political_seed123_1000t`) — must stay green/skip exactly as before; the new
  table entry is keyed to one specific `(run_key, pillar)` pair and
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` (below) is the dedicated
  guard proving no other pair is affected.
- `test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`,
  `test_information_intent_execution_fires_through_kernel_tick_once` — unrelated structural
  probes; must not regress from a shared-module edit (per the parent ticket's own Step 2
  guard note — same file, same discipline applies here).

### Unit — `tests/unit/worldassembly/test_corpus_diversity.py` (`-m slow`, 32 guards)

- `test_urban_political_seed123_1000t_social_economy_grade_stability` — must stay green,
  **unmodified** (per this ticket's Related Tickets/Out-of-Scope: no edit to this guard's
  SOCIAL/ECONOMY content unless the SOCIAL open question below is explicitly adopted into
  this ticket's scope by a planning decision — if not adopted, this guard is untouched).
- `test_frontier_marches_seed42_200t_narrative_grade_stability` — must stay green,
  unmodified; a different anchor, not touched by this ticket.
- The other 30 `-m slow` guards in the file — unaffected by any change in this ticket's scope
  (`test_grade_regression.py` only); regression coverage via a full `-m slow` run is optional
  here (expensive, ~15-20 min sequential) but recommended once as a final sanity check per the
  project's `-m slow` discipline, not required for every iteration.

### Static / architecture

- `tests/static/test_corpus_diversity_ci_isolation.py` — unrelated to this ticket's scope
  (CI-wiring guard from the parent ticket); must not regress from an unrelated import-adjacent
  edit if any shared fixture/import path is touched.

## New Tests Required

Per the ticket's Acceptance Criteria:

1. **Update `test_score_tolerance_override_table_scoped_to_named_pillars`** (not a brand-new
   test, but a required edit — listed here because the AC explicitly names it as something
   that "must pass and correctly reflect the 3-entry table"):
   - Category: unit / anti-drift guard.
   - Verifies: `set(SCORE_TOLERANCE_OVERRIDES.keys())` equals the **3**-tuple set (add
     `("urban_political_seed123_1000t", "NARRATIVE")` to the existing 2), and the new entry's
     `abs_floor` widens (not narrows) the default tolerance for its anchor score — the
     existing per-entry loop already generalizes to a 3rd entry with no logic change, only the
     hard-coded expected-set literal needs updating.
   - Location: `tests/simulation_quality/test_grade_regression.py:605-623` (edit in place).

2. **No new logic test needed for `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`**
   — it is self-adjusting (dynamically skips whatever is currently in
   `SCORE_TOLERANCE_OVERRIDES`), so adding the 3rd entry requires no edit to this test's body,
   only confirmation it still passes (regression surface, above, not a new test).

3. **`test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` passing against
   fresh, real (non-skip) calibration data** (not a new test — the existing parametrized case,
   listed here because the AC requires proving it actually passes, not just exists):
   - Category: integration (exercises the real replayed calibration report against the fixture
     + override table).
   - Verifies: with the 3rd override entry wired in and fresh calibration data regenerated at
     the default path (`data/calibration/urban_political_seed123_1000t/quality_report.json`,
     via `python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`, no
     custom `--output`), the parametrized case shows `1 passed`, not skipped, not failed.
   - Location: `tests/simulation_quality/test_grade_regression.py:313` (existing, no new code).

4. **(Conditional — only if the SOCIAL open question from investigation.md is explicitly
   adopted into this ticket's scope by a planning decision) a 4th `SCORE_TOLERANCE_OVERRIDES`
   entry for `("urban_political_seed123_1000t", "SOCIAL")`**, derived the same way, with the
   expected-set assertion in `test_score_tolerance_override_table_scoped_to_named_pillars`
   updated to 4 entries instead of 3. **Default assumption per investigation.md's
   recommendation: NOT adopted in this ticket** — disclosed only, filed as a separate
   follow-up. This item exists in this test plan only so an implementer who does receive a
   planning decision to fold SOCIAL in has the corresponding test-impact already mapped; do
   not add it speculatively.

## Scoped Pytest Commands

```bash
# Anti-drift guard + structural regression surface (fast, no calibration data needed for these)
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -v
pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -v
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v

# Fast-tier anchor sweep (no slow marker; confirms no accidental regression to other run_keys
# from the shared-module edit)
pytest tests/simulation_quality/test_grade_regression.py -k "test_grade_within_anchor_band and not long_run" -v

# Regenerate the calibration report the fix must actually pass against, then exercise it
python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000
pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v

# Full slow-tier long-run sweep for this file (confirms no other SLOW_ANCHOR_KEYS entry regressed)
pytest tests/simulation_quality/test_grade_regression.py -m slow --resource-budget large -v

# The 2 named grade_stability guards this ticket must not have touched (structural
# no-op check — confirm they still pass exactly as before)
pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" -m slow --resource-budget large -v
pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_frontier_marches_seed42_200t_narrative_grade_stability" -m slow --resource-budget large -v
```

Never `pytest tests/` — all commands above are scoped to `tests/simulation_quality/
test_grade_regression.py` and the 2 named `test_corpus_diversity.py` guards, consistent with
the project's Testing Rule.

## Anti-Drift Test Guards

- **`test_score_tolerance_override_table_scoped_to_named_pillars`** (updated, not new) is
  itself the primary anti-drift guard: it fails hard if the table grows an entry beyond the
  explicitly-expected set, or if any entry's `abs_floor` fails to actually widen the default
  tolerance (catches an implementer accidentally *narrowing* tolerance for an anchor, which
  would silently mask a real regression rather than accommodate genuine variance).
- **`test_score_tolerance_overrides_do_not_affect_unlisted_anchors`** — proves the 3rd entry
  does not leak into any other `(run_key, pillar)` pair's tolerance calculation; this is the
  test that would catch a bug where the lookup key was built wrong (e.g. matched on `pillar`
  alone, or a typo in `run_key`) and silently widened tolerance for unrelated anchors.
- **`test_grade_anchors_entry_count_unchanged`** — guards against an accidental
  `grade_anchors.json` edit; this ticket's recommended fix does not touch that file, so this
  test staying green is direct proof of that constraint holding.
- **`git diff --stat -- tests/unit/worldassembly/test_corpus_diversity.py
  tests/simulation_quality/fixtures/grade_anchors.json src/engine/kernel.py`** (ticket AC's
  own final check) — must be empty unless the SOCIAL open question is explicitly adopted and
  called out; this is the literal AC-mandated anti-drift check for this ticket's scope
  boundary and should be run as the final verification step before closing.
- **Manual diff review of `SCORE_TOLERANCE_OVERRIDES`'s 2 pre-existing entries** — confirm
  `("urban_political_seed123_1000t", "ECONOMY"): 0.2878` and
  `("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351` are byte-identical to their current
  committed values (this ticket's Out of Scope explicitly forbids re-opening either).
