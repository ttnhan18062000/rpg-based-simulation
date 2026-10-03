---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-RAWSCORE-PERSIST
phase: done
date: 2026-07-13
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260713-SIMQ-RAWSCORE-PERSIST

## Title
Persist raw `normalized_score` alongside the letter grade in `grade_anchors.json`, with its own
regression-tolerance check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`tests/simulation_quality/fixtures/grade_anchors.json` currently stores only the discretized
letter grade per pillar (confirmed: a bare string, e.g. `"S"`) — never the raw `normalized_score`
that produced it, even though every `quality_report.json` computes and prints it. Combined with S
being an unbounded top band (`quality_scoring_contract.md` §4.5: `S | >2.0 | Exceptional`, no
upper limit specified) and `test_grade_regression.py`'s comparison
(`_within_band`, line ~140) only ever checking the letter grade, this makes the regression-
detection goal blind in both directions for any pillar already at S: a real improvement (e.g.
norm-score 2.1 → 10.0) shows as "S → S", invisible — but so does a real *regression* (10.0 → 2.1)
that doesn't happen to cross a full grade-letter boundary. The anchor system can currently only
catch changes that cross a grade-letter line, not changes in magnitude within one.

**This is explicitly not the excluded Non-Goal.** SimQ's §14 rules out "historical run comparison"
(dashboards, trend charts across runs over time) — that stays out of scope, reaffirmed 2026-07-10.
This ticket is narrower: one additional number stored per anchor entry, checked with one
additional tolerance assertion, squarely inside the existing regression-detection goal (§1), not a
new comparison/analytics capability.

## Scope
- Extend `grade_anchors.json`'s per-pillar schema from a bare string (`"S"`) to an object carrying
  both grade and score (e.g. `{"grade": "S", "score": 2.87}`) — migration needed for all 72×10
  existing entries. **Sequence this to reuse `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s re-anchor
  pass — do not run a second full corpus sweep purely for this migration.**
- Extend `test_grade_regression.py`'s comparison logic to additionally assert the raw score stays
  within an empirically-determined tolerance band (e.g. a percentage or absolute delta — to be
  determined by investigation, not guessed) of the anchored value, independent of whether the
  letter grade moved.
- Update any other code that reads `grade_anchors.json` entries as bare strings (grep for
  consumers before assuming `test_grade_regression.py` is the only one — `tools/evaluate_simq.py`
  is a known second consumer).

## Out of Scope
- Any new dashboard, trend chart, or cross-run comparison UI/tooling — that is the excluded §14
  Non-Goal ("historical run comparison"), explicitly not reopened by this ticket.
- The weight/threshold recalibration itself (`TCK-20260713-SIMQ-SCORE-CEILING-FIX`) — this ticket
  only adds visibility into score magnitude; it does not change what the scores are.
- Persisting scores anywhere beyond `grade_anchors.json` (e.g. no new long-term storage of
  `data/calibration/`'s per-run reports — those remain transient/gitignored as today).

## Acceptance Criteria
- [x] `grade_anchors.json` stores both grade and raw score per pillar per anchor entry.
- [x] `test_grade_regression.py` asserts the raw score stays within a documented tolerance of the
      anchored value, in addition to the existing letter-grade band check.
- [x] A deliberately-injected synthetic score regression that stays within the same letter-grade
      band (e.g. an S-graded pillar's score cut in half but still >2.0) is caught by the new
      tolerance check — and demonstrated to NOT have been caught by the old letter-only check, as
      a concrete before/after proof this ticket closes the gap it claims to.
- [x] The chosen tolerance width is justified against real run-to-run variance data (not guessed)
      — cite `docs/audits/D20_simq_integration.md`'s wall-clock-throttle findings or equivalent
      fresh evidence.

## Related Tickets
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` — sequenced before this ticket to share one re-anchor pass.

## Related Docs
- `docs/simulation_quality/current_state.md` — Recommendation 4, the finding this ticket addresses.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 1b, this ticket's source.
- `docs/simulation_quality/quality_scoring_contract.md` §4.5 (grade bands, S is unbounded), §14
  (Non-Goals — confirm this ticket's scope stays narrower than the excluded item), §1 (goals).
- `docs/audits/D20_simq_integration.md` — wall-clock-throttle run-to-run variance findings, needed
  to justify the tolerance width.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` (`_within_band`, line ~140; `GRADE_ORDER`,
  line ~34)
- `tools/evaluate_simq.py` (a second known consumer of the anchor file's schema — confirm no
  others exist before assuming these two are the full consumer set)

## Assumptions / Open Questions
- The exact tolerance width (percentage vs. absolute delta, and its numeric value) is not yet
  determined — first investigation task, informed by real variance data, not guessed.
- Whether the schema migration is a one-time script or needs to be re-derivable (e.g. re-running
  the corpus sweep regenerates both fields together) is left to the implementer.

## Implementation Notes
Followed staging_artifacts/TCK-20260713-SIMQ-RAWSCORE-PERSIST/plan.md's 9 steps in order.

1. **Migration**: One-time script (scratch, not committed) migrated all 75 non-metadata
   entries in `grade_anchors.json` from bare grade strings to `{"grade": ..., "score": ...}`
   objects, reading `score` from `data/calibration/{run_key}/quality_report.json`'s
   `pillars.{PILLAR}.normalized_score` (confirmed on disk for all 75 keys before running).
   Sanity-checked: 75 entries preserved, every pillar value a dict with exactly
   `{grade, score}`, and every migrated grade string byte-identical to its pre-migration
   value (only the value's type changed).
2. Rewrote `_instructions` metadata text to describe both the new object schema and the
   two independent checks (letter band ±1, score tolerance).
3. Fixed the three anchor-read call sites in `test_grade_regression.py`
   (`test_grade_within_anchor_band`, `test_grade_within_anchor_band_long_run`,
   `test_urban_political_selfmodel_cognition_isolated_grade_anchor`) to read
   `anchor["grade"]`/`anchor["score"]`. Added a new `_extract_pillar_scores()` helper
   (mirrors `_extract_pillar_grades()`, reads `normalized_score` from the live report) since
   the plan's new tolerance check needs the live score, not just the live grade — this
   helper wasn't explicitly named in the plan text but is a direct, minimal consequence of
   Step 4's requirement. Rewrote `test_grade_anchor_file_exists_and_valid`'s per-pillar
   assertion to check the `{grade, score}` shape and added the field-confusion guard using
   `hero_guild_routing_seed42_1000t`/NARRATIVE (grade S, score 3.19, confirmed != its
   raw_score 3190.0 in the calibration report).
4. Added `SCORE_TOLERANCE_ABS_FLOOR = 0.05`, `SCORE_TOLERANCE_REL_PCT = 0.20`, and
   `_within_score_tolerance()` next to `_within_band()`. Folded an additional,
   independently-asserted score-tolerance check into all three anchor-band test functions,
   with separate failure lists (`band_failures` / `score_failures`) so a CI reader can tell
   the two regression types apart. Verified `_within_band.__defaults__ == (1,)` unchanged.
5. Added `test_score_tolerance_catches_within_band_regression()` — synthetic anchor
   `{"grade": "S", "score": 4.5}` vs. live `2.25` (half, still S-band): proves the old
   `_within_band("S","S")` passes (gap) while the new `_within_score_tolerance(2.25, 4.5)`
   fails (catches it).
6. Fixed `tools/evaluate_simq.py::main()`'s one call site
   (`anchor_grades = {p: v["grade"] for p, v in all_anchors[run_key].items()}`) —
   `_compare()`/`_within_band()` untouched, still bare-string. Added
   `TestAnchorSchemaCompat` to `test_evaluate_harness.py`: one test proving the extraction
   line produces identical `_compare()` inputs to the old bare-string schema, and one
   `--dry-run --scenario sandbox_world_seed42_200t` smoke test invoking the real `main()`
   against the real post-migration fixture and calibration data (asserts `SystemExit(0)`
   and "0 regressions" in stdout).
7. Updated `quality_scoring_contract.md` §11.3 to describe the two independent regression
   dimensions (letter-band ±1, unchanged; new score-tolerance, with its formula and
   empirical derivation). §11.6, §4.4, §4.5, §14 untouched.
8. Updated `docs/parity_ledger/infrastructure.yaml`'s `INFRA-250` (new schema + tolerance
   dimension, added `test_score_tolerance_catches_within_band_regression` to `test_path`)
   and `INFRA-252` (schema-compat fix note, added `TestAnchorSchemaCompat` to `test_path`).
   Left the pre-existing "25 entries" staleness untouched (out of scope, per plan).
9. Updated `.claude/workflows/simq-audit.js`'s anchor-updater prompt text (~line 219) to
   mention updating both `grade` and `score` fields, reading `score` from
   `normalized_score` not `raw_score`.

Ran `make knowledge-index-update` (docs/ modified) and `graphify update .` (tests/ modified)
per the After Work rule.

No deviations from plan.md beyond the one addition noted in Step 3 above
(`_extract_pillar_scores()` helper) — recorded in plan.md's Deviations section.

**Post-DoD-check addition (2026-07-14):** test_plan.md's two Anti-Drift Test Guards
(`_within_band`'s default tolerance unchanged; `grade_anchors.json`'s total entry count
unchanged post-migration) had only been verified manually during implementation, not as
committed automated tests — flagged by done-checker as a "material gap unstated." Added
`test_within_band_default_tolerance_unchanged` and
`test_grade_anchors_entry_count_unchanged` to `test_grade_regression.py` to close this
gap; both pass.

## Test Summary
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — 59 passed
  (structural, band, and score-tolerance checks against migrated fixture).
- `pytest tests/simulation_quality/test_grade_regression.py -m slow` — 18 passed (long-run
  anchors, same checks).
- `pytest tests/simulation_quality/test_evaluate_harness.py` — 22 passed (existing
  `TestWithinBand`/`TestCompare`/`TestParseRunKey`/`TestResolveWorldName` unchanged and
  green, plus new `TestAnchorSchemaCompat` (2 tests)).
- Confirmed pre-existing, unrelated failures in
  `tests/unit/worldassembly/test_corpus_diversity.py`
  (`test_module_family_anchored`, `test_generated_frontier_3_42_extended_population_stability`)
  reproduce identically on `git stash` (before this ticket's changes) — a missing
  `data/worlds/urban_political_selfmodel_probe/world.yaml` directory and known engine
  tick-throttle nondeterminism, both out of this ticket's scope.
- `pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged
  tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v`
  — 2 passed (added post-DoD-check; previously only manually verified during
  implementation, now committed automated guards per test_plan.md).

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py`
- `tests/simulation_quality/test_evaluate_harness.py`
- `tools/evaluate_simq.py`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/parity_ledger/infrastructure.yaml`
- `.claude/workflows/simq-audit.js`

## Completion Summary
All 4 acceptance criteria met: (1) `grade_anchors.json` now stores `{grade, score}` per
pillar per anchor entry (75/75 entries migrated, using `normalized_score` not
`raw_score`); (2) `test_grade_regression.py` asserts a documented, independent score
tolerance (`abs_delta <= max(0.05, 0.20 * |anchored_score|)`) alongside the existing
letter-band check in all three anchor-band test functions; (3) a dedicated synthetic
before/after test (`test_score_tolerance_catches_within_band_regression`) proves the new
check catches a within-band 50%-magnitude regression that the old letter-only check
passes; (4) the tolerance width is justified against this session's 18-run_key/180-
observation same-config repeat-trial dataset (cited in the plan, the contract doc, and
the parity ledger). The only other bare-string consumer, `tools/evaluate_simq.py`, got
its minimal schema-compat fix (score-tolerance mirroring explicitly deferred, per
plan.md's Anti-Drift Notes). No P0 parity entries touched; no fresh corpus sweep run
(reused the sibling `SCORE-CEILING-FIX` ticket's already-regenerated calibration
reports).
