---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY
artifact_type: test_plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Test Plan — TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY

## Regression Surface

This ticket touches test/fixture files, not engine code, so the regression surface is narrow but
must be run against the freshly re-generated `data/calibration/` reports (all 18 keys are
gitignored/ephemeral — see investigation.md).

**Unit / fixture-structure:**
- `tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid` —
  must keep passing after any `grade_anchors.json` edit; asserts every `FAST_ANCHOR_KEYS` entry has
  exactly 10 pillar grades, all in `GRADE_ORDER`. This ticket's scope explicitly does not expect
  `grade_anchors.json` value edits (only a genuine drift finding would trigger one, out of scope
  per AC), but the structural test must still pass.
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band` (fast tier,
  `FAST_ANCHOR_KEYS`, 55 keys) — must not regress; this ticket is explicitly scoped to
  `SLOW_ANCHOR_KEYS` only (AC: "Any FAST_ANCHOR_KEYS entries... are out of scope"), so fast-tier
  results must be unaffected by any test/fixture change here.

**Slow / long-run tier (the direct object of this ticket):**
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run`
  (`@pytest.mark.slow`, all 18 `SLOW_ANCHOR_KEYS`) — every key must pass against its (possibly
  re-verified, possibly re-anchored) grade after this ticket's re-runs.

**World-corpus / population-stability guards (`tests/unit/worldassembly/test_corpus_diversity.py`):**
- `test_population_stability` (parametrized over `POPULATION_STABILITY_WORLDS`, includes
  `dungeon_crawl`, `sandbox_world`, `urban_political`, `generated_frontier_3_42`,
  `unit_faction_tension`, `unit_selfmodel_pilot`, `hero_guild_routing` — all worlds this ticket's
  keys touch) — 300-tick, 60%-floor guard; must not regress from re-running calibration (this
  ticket does not touch world content or the engine).
- `test_generated_frontier_3_42_extended_population_stability` (`@pytest.mark.slow`, lines
  289-374) — the existing tolerance-guard precedent for the pattern any "unstable" key conversion
  must follow; must keep passing unmodified unless this ticket's own findings require adjusting its
  thresholds (not expected — this ticket does not re-litigate population floors, only grade
  stability).
- `test_hazard_kind_matches_populating_faction_immunity` (`HAZARD_KIND_MATCH_WORLDS =
  ["dungeon_crawl", "urban_political", "generated_frontier_3_42"]`) — unrelated content guard;
  included in regression surface only because it shares a test file with any new tolerance-guard
  test this ticket adds, to confirm no import/fixture-level breakage.

**Integration (indirect, run to confirm no accidental config/profile drift):**
- Any test importing `src/simulation_quality/weights.py::ScoringWeights.load` against
  `config/simulation_quality/scoring_weights.yaml` / `grade_thresholds.yaml` /
  `detection_params.yaml` — this ticket must not edit those config files; if a re-run produces an
  unexpected grade shift traceable to a config drift (not throttle timing), that is the "genuine
  behavior divergence" the ticket's AC requires escalating as a separate ticket, not silently
  absorbing.

## New Tests Required

Exact shape depends on the Plan phase's decision on how many (of the 18) keys classify "unstable"
and how tolerance-guard conversion should be structured (see investigation.md Risks — the
tolerance-range schema gap in `grade_anchors.json` is an open Plan-phase decision). At minimum:

1. **Per-key reliability re-verification (not a new automated test — a manual/scripted re-run +
   documentation step).** Category: process/documentation, not a pytest test. For each of the 18
   `SLOW_ANCHOR_KEYS`, run `tools/calibrate_simq.py` 2-3× at the key's existing seed/ticks/profile
   (see investigation.md's invocation table), record the per-pillar grade from each trial, and
   classify stable / unstable per the ±1-`GRADE_ORDER`-band rule already enforced by
   `test_grade_within_anchor_band_long_run`. Lives in `docs/simulation_quality/eval_matrix_results.md`
   (new "Reliability Status" subsection or per-world note, per the ticket's Scope).

2. **Grade-stability multi-trial guard(s) for any key classified "unstable".** Category:
   architecture-guard / regression (mirrors `test_generated_frontier_3_42_extended_population_stability`'s
   pattern but for grades, not population). What it verifies: across N (2-3) independent same-seed
   trials of the real, throttled `Kernel`, a given world/tick-count's per-pillar grade never falls
   outside the anchor's existing ±1-letter band — i.e. the anchor is trustworthy under wall-clock
   variance, not just lucky on one draw. Where it lives: `tests/unit/worldassembly/
   test_corpus_diversity.py`, `@pytest.mark.slow`, following the naming convention
   `test_{world}_{ticks}t_grade_stability` (or equivalent) for each unstable key's world/tick-count
   pair (not necessarily one test per seed — the existing precedent groups seeds, not per-seed
   tests). **If the Plan phase determines zero keys classify "unstable"** (plausible — the single
   confirmatory re-run performed during investigation matched the anchor exactly), this test
   category may end up empty; that is a valid outcome per the ticket's own three-way classification
   (stable / converted-to-tolerance / flagged-unverified) and must still be documented as such, not
   silently skipped.

3. **Coverage/structural check that all 18 keys received a documented reliability status.**
   Category: unit / documentation-completeness guard. What it verifies: a lightweight test (or a
   `tools/simq_audit_gaps.py` extension, if that tool already scans `eval_matrix_results.md` for
   anchor coverage — confirm at Plan/Implement time) that every `SLOW_ANCHOR_KEYS` entry has a
   corresponding reliability-status note in `eval_matrix_results.md`. Where it lives: either a new
   assertion appended to `test_grade_anchor_file_exists_and_valid`'s spirit (a parallel check
   against the doc, not the fixture) or a standalone test in `test_grade_regression.py`. This is
   the acceptance-criteria completeness gate — flag to the Plan phase as optional-but-recommended
   given the ticket's AC explicitly requires "every one of the 18 keys" to have a status; an
   automated check prevents silent partial completion.

## Scoped Pytest Commands

```
# Slow-tier grade regression (the direct object of this ticket) — all 18 SLOW_ANCHOR_KEYS
pytest tests/simulation_quality/test_grade_regression.py -m slow

# Fast-tier regression must remain unaffected (explicitly out of scope; confirm no collateral drift)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"

# Structural fixture-validity check (must pass regardless of which keys change)
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid

# World-corpus population-stability guards for every world this ticket's keys touch, plus the
# existing tolerance-guard precedent and any new grade-stability guard(s) added under this ticket
pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow
pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"

# Full scoped sweep for this ticket's own two touched test files, both tiers
pytest tests/simulation_quality/test_grade_regression.py tests/unit/worldassembly/test_corpus_diversity.py -q

# The ticket AC's "make evaluate-full or equivalent scoped regression sweep" — per investigation.md,
# `make evaluate-full` alone does NOT exercise SLOW_ANCHOR_KEYS (fast-tier only, ≤500t). Use the
# slow-tier-inclusive equivalent instead:
make simq-full-audit-slow
# (equivalent to: pytest tests/simulation_quality/test_grade_regression.py -q — fast + slow, unfiltered)

# If new/modified tolerance-guard tests are added to test_corpus_diversity.py, run them explicitly:
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "grade_stability" -m slow -v
```

Never run bare `pytest tests/` — scope stays within `tests/simulation_quality/` and
`tests/unit/worldassembly/test_corpus_diversity.py` per this ticket's Related Code Areas.

## Anti-Drift Test Guards

- **Fast-tier isolation guard**: `pytest tests/simulation_quality/test_grade_regression.py -m "not
  slow"` must show zero change in pass/fail counts before and after this ticket's edits — any drift
  here would indicate the ticket accidentally touched `FAST_ANCHOR_KEYS` or shared fixture-loading
  code, which is explicitly out of scope.
- **`kernel.py` zero-diff guard**: `git diff --stat src/engine/kernel.py` (or equivalent CI check)
  must report no changes at Implement-phase completion — this is the ticket's own hard AC, not just
  a convention. Any test suite reporting a *different* grade than a prior committed anchor should
  first be checked against this diff, not assumed to be a genuine finding, since an accidental
  kernel edit would also explain a grade shift.
- **`grade_anchors.json` schema-integrity guard**: `test_grade_anchor_file_exists_and_valid` must
  keep passing after any edit — guards against a tolerance-range representation accidentally
  breaking the existing single-grade-string schema (e.g. writing a list or dict where a string is
  expected), which the investigation flagged as a live risk if the Plan phase chooses a
  fixture-schema change over a separate-test-only conversion.
- **No content/config collateral-edit guard**: `git diff --stat data/content/ config/
  data/worlds/` should show no changes — this ticket's scope is test/fixture/doc only; any content
  or world-compile drift found during re-runs must be reported as a separate ticket per the
  ticket's own Assumptions section, not silently fixed in-line here.
- **Reliability-status completeness guard**: before closing the ticket, a final grep/scan of
  `docs/simulation_quality/eval_matrix_results.md` should confirm all 18 `SLOW_ANCHOR_KEYS` string
  values appear with an associated stable/converted-to-tolerance/flagged-unverified marker — catches
  silent partial completion (e.g. 15 of 18 keys documented, 3 forgotten) that no existing automated
  test currently checks for (see New Test #3 above for making this a standing guard rather than a
  one-time manual check).
- **`evaluate-full` mis-scoping guard**: if the Implement/Verify phase reports "`make evaluate-full`
  passed, 0 regressions" as evidence this ticket's AC is satisfied, that claim must be cross-checked
  against `make simq-full-audit-slow` (or `pytest ... -m slow`) actually having been run too — per
  investigation.md, `evaluate-full` alone never exercises any of the 18 keys this ticket is about
  and would give a false-positive "0 regressions" signal.
