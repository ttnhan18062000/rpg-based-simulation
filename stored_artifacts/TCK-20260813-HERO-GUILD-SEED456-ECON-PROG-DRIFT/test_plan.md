---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus, economy, progression]
---

# Test Plan — TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT

## Regression Surface

This is a fixture-only recalibration (no source changes proposed — see investigation.md Risks #5).
The regression surface is therefore the fixture-consuming test modules themselves, to prove the
edit doesn't corrupt fixture shape or silently touch an unrelated (run_key, pillar) pair.

**Unit — fixture structure/anti-drift guards** (`tests/simulation_quality/test_grade_regression.py`):
- `test_grade_anchor_file_exists_and_valid` — must still pass; confirms the edited entries keep the
  `{"grade", "score"}` shape and `grade` stays a valid `GRADE_ORDER` member.
- `test_grade_anchors_entry_count_unchanged` — must still pass at 81 scenario entries; this ticket
  edits existing pillar fields inside 2 existing run_key entries, it does not add/remove a run_key.
- `test_score_tolerance_override_table_scoped_to_named_pillars` — must still pass **unchanged**; per
  investigation.md Risk #2, this ticket must NOT add a `SCORE_TOLERANCE_OVERRIDES` entry, so this
  guard's exact-5-entry assertion must not need editing.
- `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` — must still pass; confirms the
  new `simq_routing_test_seed456_500t`/PROGRESSION anchor value correctly falls through to the
  global default tolerance (no override).
- `test_score_tolerance_catches_within_band_regression`, `test_grade_order_includes_f_band`,
  `test_within_band_default_tolerance_unchanged` — unrelated synthetic-value guards, must stay green
  untouched.

**Unit — `score_ceilings.json`/`simq_ceiling.py` structure** (`tests/tools/test_score_ceilings.py`):
- All 5 existing tests (`test_tick_budget_ceiling_flags_short_scenarios`,
  `test_tick_budget_covers_confirmed_time_gates`, `test_flag_gated_combat_ceiling_present`,
  `test_ceiling_lookup_returns_none_for_unclassified_pair`, `test_corrected_narrative_entry_present`,
  `test_grade_regression_failure_message_includes_ceiling_when_known`) must stay green — none
  reference `simq_routing_test_seed456_500t` or `hero_guild_routing_seed456_500t` by name, so the
  new `score_ceilings.json` entry should not perturb any of them; run as a direct confirmation.

**Integration — the ticket's own named scope** (`tests/simulation_quality/test_grade_regression.py`):
- `test_grade_within_anchor_band[hero_guild_routing_seed456_500t]`
- `test_grade_within_anchor_band[simq_routing_test_seed456_500t]`

**Full fast-tier cross-contamination check** (before/after `-m "not slow"` full sweep, matching the
parent ticket's own established `git stash`/`git stash pop` A-B comparison precedent — see
`stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/plan.md` Deviations):
confirm the full `FAST_ANCHOR_KEYS` sweep's total failed/passed count changes by exactly the
expected delta (this ticket's edits should flip 0-2 pytest outcomes to green for the two touched
`run_key` parametrizations — see "Expected pytest outcome" below, since COMBAT/WORLD failures on
`hero_guild_routing_seed456_500t` and COMBAT on `simq_routing_test_seed456_500t` are pre-existing
and unaffected by this ticket) and zero unrelated (run_key, pillar) pairs newly fail.

## New Tests Required

No new test *code* is required — this is a pure fixture-value recalibration (`grade_anchors.json`)
plus one new fixture *entry* (`score_ceilings.json`), not new source behavior. The existing
parametrized `test_grade_within_anchor_band[hero_guild_routing_seed456_500t]` and
`test_grade_within_anchor_band[simq_routing_test_seed456_500t]` already provide full coverage of
every pillar on both run_keys, including the 3 fields this ticket recalibrates — adding a
narrower, duplicate test would not test anything the existing parametrization doesn't already
cover.

If Plan/Implement judges a dedicated guard is still warranted (e.g. to pin the new
`score_ceilings.json` entry's exact `run_key`/`pillar`/`ceiling_kind` against silent future
deletion, matching the style of `test_flag_gated_combat_ceiling_present` /
`test_corrected_narrative_entry_present` in `tests/tools/test_score_ceilings.py`), it would be:

- **Test name**: `test_watchdog_variance_ceiling_present_for_simq_routing_test_seed456_progression`
- **Category**: unit
- **What it verifies**: `simq_ceiling.lookup_ceiling("simq_routing_test_seed456_500t",
  "PROGRESSION")` returns a `CeilingInfo` with `ceiling_kind == "watchdog_variance"` and
  `since_ticket == "TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT"`, mirroring
  `test_flag_gated_combat_ceiling_present`'s shape.
- **Where it should live**: `tests/tools/test_score_ceilings.py` (append)

This is optional/Plan's call, not a hard requirement — flagged here per test_plan.md convention,
not mandated.

## Scoped Pytest Commands

Primary verification (the ticket's own Acceptance Criteria command, run verbatim):

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k \
  "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"
```

**Expected outcome after recalibration — read this carefully, it is NOT "0 failed":**

Per investigation.md Risk #3, both parametrizations of `test_grade_within_anchor_band` will likely
**still show FAILED** after this ticket's fixture edits land, because each run_key carries at least
one *pre-existing, already-known, out-of-this-ticket's-scope* score-tolerance failure that this
ticket does not touch:
- `hero_guild_routing_seed456_500t`: COMBAT (`[known flag_gated]`) and WORLD (`[known tick_budget]`)
  remain failing — both automatically, correctly annotated by `tools/simq_ceiling.py`'s computed
  classifiers, independent of any `grade_anchors.json` edit.
- `simq_routing_test_seed456_500t`: COMBAT (`[known flag_gated]`) remains failing; PROGRESSION
  itself may *also* still show as failing on an unlucky future draw (`[known watchdog_variance]`,
  once the new `score_ceilings.json` entry exists) — this is the intended, disclosed end-state per
  Finding 2, not a leftover gap.

**The correct acceptance check is therefore textual, not exit-code-based**: run the command above
and confirm every line inside each failure's `score_failures` list carries a trailing `[known ...]`
annotation. Zero *unannotated* lines is "0 unexplained failures" per the ticket's AC wording; an
unannotated `ECONOMY` or `PROGRESSION` line (missing the `[known ...]` suffix) means the
`grade_anchors.json` edit did not take effect or was computed against stale/instrumented data
(investigation.md Risk #4) and must be re-derived from a fresh, clean (non-DEBUG-instrumented)
`tools/calibrate_simq.py` run before re-attempting.

Regression/anti-drift guards (run together, scoped to the fixture-consuming modules only — never
`pytest tests/` repo-wide):

```
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid \
  tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged \
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars \
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors \
  tests/tools/test_score_ceilings.py \
  -q -m "not slow"
```

Full fast-tier cross-contamination sweep (before/after comparison, `git stash`/`git stash pop`
around the `grade_anchors.json`/`score_ceilings.json` edits — requires all 89 `FAST_ANCHOR_KEYS`'
`data/calibration/*/quality_report.json` files present, matching the parent ticket's own precedent):

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

Never run `pytest tests/` repo-wide (CLAUDE.md Testing Rule) and never run
`tests/unit/worldassembly/test_corpus_diversity.py -m slow` as a raw sequential sweep (unrelated to
this ticket's `_500t`-only scope; the `_1000t` guard family was already closed by the parent
ticket).

## Anti-Drift Test Guards

- `test_score_tolerance_override_table_scoped_to_named_pillars` (existing) — the load-bearing guard
  against this ticket accidentally widening `SCORE_TOLERANCE_OVERRIDES` instead of doing a plain
  point-edit + `score_ceilings.json` annotation (investigation.md Risk #2's explicit warning). If
  Implement's diff touches this guard's own assertion, that is itself a signal the wrong mechanism
  was used.
- `test_grade_anchors_entry_count_unchanged` (existing) — catches an accidental new/dropped
  `grade_anchors.json` run_key entry; this ticket must only mutate existing pillar values inside the
  2 already-present `hero_guild_routing_seed456_500t`/`simq_routing_test_seed456_500t` entries.
- Full `FAST_ANCHOR_KEYS` before/after sweep (Regression Surface, above) — the guard against this
  ticket's edit silently perturbing any of the other ~87 `(run_key)` parametrizations sharing the
  same fixture file; must show identical pass/fail status on every key other than the 2 named ones.
- Manual diff review of `grade_anchors.json` and `score_ceilings.json` before commit, confirming:
  (a) only `hero_guild_routing_seed456_500t.{ECONOMY,PROGRESSION}` and
  `simq_routing_test_seed456_500t.PROGRESSION` changed in `grade_anchors.json` — every other pillar
  on both run_keys, and every other run_key, byte-identical; (b) `score_ceilings.json` gained
  exactly one new entry (`simq_routing_test_seed456_500t`/PROGRESSION/`watchdog_variance`), and the
  existing 6 entries are byte-identical (per the parent ticket's own "annotate only, preserve audit
  history" precedent — never delete an existing ceiling entry).
- `tests/simulation_quality/test_economy_scorer.py` and
  `tests/simulation_quality/test_progression_scorer.py` (unit-level scorer tests, construct
  synthetic envelopes directly) — must stay green, unmodified, throughout. Per investigation.md
  Finding 1, this ticket does not touch `EconomyScorer`/`ProgressionScorer`'s own scoring logic; if
  either of these test files needs to change, that is a signal the change went beyond the intended
  fixture-only scope.
