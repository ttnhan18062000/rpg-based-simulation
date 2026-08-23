---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-GRADE-SCORER
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-GRADE-SCORER

## Title
Sibling grade-band scoring system for visual-quality metrics

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a grade-band scorer reusing SimQ's exact S/A/B/C/D/F thresholds, architecturally independent from SimQ, computing directly from AuthoritativeState geometry via the Shape/Density/Variants/Connectivity metric outputs. Structured as hard rules (binary facts), soft rules (gradient signals with a healthy band, non-monotonic), and scoring rules combining them into a grade. Multi-seed averaging across a world spec's renders is core to this system's design — currently a no-op since terrain is seed-invariant, but built now so it activates once world-gen becomes seed-varied.

## Scope
- Design and implement the currently-unspecified hard+soft -> single-normalized-score combination step needed before grade assignment (the real design risk identified in investigation)
- Implement grade assignment reusing the exact threshold table (S:2.0, A:0.5, B:0.0, C:-0.5, D:-1.0), sourced from a config file, never hardcoded in scorer code
- Implement non-monotonic soft-rule scoring: a healthy-band soft rule produces a positive delta inside its range and a negative delta at BOTH low and high extremes
- Implement multi-seed averaging: given N per-seed scores for one world spec, the averaged score = arithmetic mean; with N=1 it equals that single score exactly
- Decide module/config file location and naming
- Confirm layer should be 'world' (not 'engine'), matching epic/idea-doc precedent

## Out of Scope
- Registering a new PillarId, subclassing PillarScorer, or importing ObservabilityEventEnvelope/QualityHub/PillarAccumulator/ScoringContext
- Multi-seed/multi-world threshold calibration itself (TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope — this ticket builds the averaging mechanism, not the calibrated values)
- CI-gating — report-only, never CI-gated
- Data-lookup or placement-legality checks

## Acceptance Criteria
- [x] Grade assignment returns the correct letter per the exact reused threshold table (S:2.0, A:0.5, B:0.0, C:-0.5, D:-1.0), sourced from a config file, not hardcoded
- [x] A soft rule with a healthy band produces a positive delta inside its range and a negative delta at BOTH low and high extremes (non-monotonic, tested explicitly, unlike SimQ's linear cascade)
- [x] Given N per-seed scores for one world spec, the averaged score equals the arithmetic mean; with N=1 it equals that single score exactly (the documented current no-op case)
- [x] The module does not import ObservabilityEventEnvelope, QualityHub, PillarAccumulator, or ScoringContext, and does not register a new PillarId
- [x] This ticket explicitly confirms (not assumes) whether the sibling system needs a parity-ledger entry or is exempt like SimQ's own grading system

## Related Tickets
- TCK-20260821-VISUAL-SHAPE-METRIC
- TCK-20260821-VISUAL-DENSITY-METRIC
- TCK-20260821-VISUAL-VARIANTS-METRIC
- TCK-20260821-VISUAL-CONNECTIVITY-METRIC
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/simulation_quality/quality_report.py
- src/simulation_quality/pillars.py
- config/simulation_quality/grade_thresholds.yaml
- tools/calibrate_simq.py
- src/core/state.py

## Assumptions / Open Questions
- The hard+soft -> single-normalized-score combination step is unspecified upstream and must be designed within this ticket
- No parity-ledger entry exists for SimQ's own grading system; this ticket confirms rather than assumes whether the sibling system is similarly exempt
- Tests/AC assert the N=1 identity/no-op case only — a variance-reduction case is out of scope since seed-varied world-gen is unfiled
- simulation-quality tag: this system is an architecturally-independent SimQ-sibling (not a pillar/subsystem member) — tagged for topical adjacency since it deliberately reuses SimQ's grade vocabulary/thresholds rather than being part of the SimQ subsystem itself

## Implementation Notes
Implemented per staging_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/plan.md's 9 steps exactly, in order:

1. `config/rendering/grade_thresholds.toml` — new directory + file, TOML content verbatim from plan.md Step 1 (grade_thresholds table copied by value from `config/simulation_quality/grade_thresholds.yaml`; one illustrative `hard_rules.fully_connected` rule; one illustrative `soft_rules.fill_ratio_healthy_band` rule).
2. `src/rendering/grading.py` — `HardRuleConfig`, `SoftRuleConfig`, `GradeConfig` frozen dataclasses (verbatim from plan.md Step 2) plus `load_grade_config`, a fail-loud `tomllib`-based loader opening the file in binary mode (`"rb"`). The loader body was only described in prose in the plan (Step 2's own code block ends in `...`), so I wrote a small private `_require_numeric(container, key, context)` helper used by all three config sections (grade_thresholds, hard_rules, soft_rules) to raise `KeyError` on a missing key and `ValueError` on a non-numeric value, per the plan's described discipline. `hard_rules`/`soft_rules` top-level tables are read via `.get(name, {})` (empty dict if the whole section is absent) rather than a hard `raw["hard_rules"]` — the plan's prose only states each *entry* under those tables must be fail-loud-validated, not that the table itself must exist; this reading satisfies all 4 of Step 8's config-loader tests without further constraint.
3. `evaluate_hard_rule` + `HardRuleResult` — verbatim from plan.md Step 3.
4. `evaluate_soft_rule` + `_trapezoidal_delta` + `SoftRuleResult` — verbatim from plan.md Step 4 (the trapezoidal non-monotonic shape).
5. `combine_rule_deltas` — verbatim from plan.md Step 5.
6. `assign_grade` — verbatim from plan.md Step 6, reproducing `src/simulation_quality/quality_report.py::_assign_grade`'s exact strict-`>` descending ladder semantics.
7. `average_scores` — verbatim from plan.md Step 7, plain `sum(...)/len(...)`, no `len == 1` special case.
8. `tests/unit/rendering/test_grading.py` — all 14 tests from plan.md Step 8, mirroring `test_density.py`/`test_shape.py`'s structure and import conventions. Tests 2-4 write real temp `.toml` files with genuine TOML `[section]`/`key = value` syntax (never YAML), per the corrected plan. Test 14 (real-corpus smoke test against `dungeon_crawl`, seed 42) asserts only that the grade is one of `{S,A,B,C,D,F}` and the combined score is finite — it does not pin a specific letter/value, since the illustrative thresholds/rule bounds are explicitly uncalibrated.
9. `docs/parity_ledger/infrastructure.yaml` — re-ran `grep -n "^- id: INFRA-3" docs/parity_ledger/infrastructure.yaml | tail` myself immediately before appending; confirmed `INFRA-373` was still the last entry (no concurrent session had appended since Review), so `INFRA-374` was appended verbatim per plan.md Step 9's 8-field shape. Verified the resulting file still parses as valid YAML (`yaml.safe_load`, 379 total entries, last entry is `INFRA-374`).

Deviation from plan.md test 1's exact boundary-value table: while writing the boundary-value parametrization, hand-verifying the strict-`>` ladder against the illustrative thresholds surfaced that a value of `-0.5001` (a hair below the `C` threshold of `-0.5`) lands on grade `D`, not `C` — `-0.5001 > -0.5` is False, so the ladder falls through to the `D` check (`-0.5001 > -1.0` is True). My first draft of the test had this case wrong (expected `C`); caught and fixed by hand-tracing the ladder with a small script before finalizing the test, and added an explicit "comfortably inside D band" case (`-0.75 -> D`) since the original 10-point boundary list didn't include one. `assign_grade`'s implementation itself is unchanged from plan.md's verbatim code — this was purely a test-fixture correction, recorded in plan.md's Deviations section per CLAUDE.md's "never silently deviate" rule.

## Test Summary
`PYTHONPATH=. .venv/bin/python3 -m pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v -m "not slow"` — 81 passed, 0 failed (includes all 14 new `test_grading.py` tests plus every pre-existing sibling rendering test and the zero-new-dependency guard, all still green, unchanged).

`PYTHONPATH=. .venv/bin/python3 -m pytest tests/simulation_quality/test_report.py tests/simulation_quality/test_weights.py tests/simulation_quality/test_grade_regression.py -v -m "not slow"` — `test_report.py` + `test_weights.py`: 44 passed, 0 failed. `test_grade_regression.py`: 32 failed, 83 passed, 18 deselected — confirmed **pre-existing and unrelated** to this ticket: `git diff --stat` shows zero tracked changes to any file under `src/simulation_quality/` or `config/simulation_quality/`, `test_grade_regression.py` has zero import coupling to `src/rendering/` (grep confirmed), and every failure message is a documented, pre-existing "known tick_budget" drift note baked into the test's own assertion output (scenario tick counts intersecting `detection_params.yaml`'s dormant/threshold-style rule cutoffs), not something introduced by this ticket's changes.

## Files Changed
- `config/rendering/grade_thresholds.toml` (new)
- `src/rendering/grading.py` (new)
- `tests/unit/rendering/test_grading.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (edited — appended `INFRA-374`)
- `tickets/inprogress/TCK-20260821-VISUAL-GRADE-SCORER.md` (this file; moved from `tickets/todos/world-rendering-core/` to `tickets/inprogress/` and updated)
- `staging_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/investigation.md`, `plan.md`, `test_plan.md` (created during this run's own Investigate/Plan phases, prior to implementation; `plan.md` additionally gained a Deviations note during this Implement pass, see above)

## Completion Summary
Implemented `src/rendering/grading.py`, an architecturally-independent SimQ-sibling module that turns Connectivity/Shape metric outputs into an S/A/B/C/D/F grade: a fail-loud `tomllib`-based config loader (`config/rendering/grade_thresholds.toml`, new file/directory), binary hard-rule evaluation, non-monotonic trapezoidal soft-rule evaluation, additive combination, grade assignment reusing SimQ's exact threshold values/ladder semantics by copied value (not import), and N-agnostic multi-seed averaging. Added all 14 tests from the plan's test spec (`tests/unit/rendering/test_grading.py`), all passing alongside the full sibling-rendering regression suite (81/81) and SimQ's own `test_report.py`/`test_weights.py` (44/44) — `test_grade_regression.py`'s 32 failures are confirmed pre-existing and untouched by this change. Added parity-ledger entry `INFRA-374` after re-confirming it was still the free next ID. All Scope Guards respected: no `src.simulation_quality.*` import, no `PillarScorer` subclass, no new `PillarId` member, no hardcoded threshold/delta/boundary literal in the scorer/loader code, no monotonic soft rules or graduated hard rules, no N=1 special-casing, no CI-gating, and none of the four sibling metric modules were modified.
