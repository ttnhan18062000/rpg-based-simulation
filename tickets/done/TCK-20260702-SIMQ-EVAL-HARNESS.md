---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-EVAL-HARNESS
phase: done
date: 2026-07-02
tags: [simq, evaluation, harness, make-target, grade-regression, quality-gate]
---

# TCK-20260702-SIMQ-EVAL-HARNESS

## Title
SimQ Standing Evaluation Harness — `make evaluate` Quality Gate

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
SimQ currently exists as a calibration artifact: you run `tools/calibrate_simq.py` manually, inspect `quality_report.json` by hand, and hope nothing regressed. There is no standing quality gate. This ticket creates one: a `tools/evaluate_simq.py` script and a `make evaluate` Makefile target that run a canonical scenario set, compare output grades against `grade_anchors.json`, and print a human-readable pass/fail table. Non-zero exit if any pillar regresses beyond ±1 band. This makes SimQ useful on every significant engine change, not just after ad-hoc calibration sessions.

Note: `test_grade_regression.py` already checks calibration data on disk, but it does not re-run the simulations. The harness fills that gap — it runs the engine, scores it, then checks the grades.

## Scope
1. New script `tools/evaluate_simq.py`:
   - Reads canonical scenario list (default: all FAST_ANCHOR_KEYS from `test_grade_regression.py`, or a configurable subset)
   - For each scenario: runs `calibrate_simq.py` logic inline (or subprocess) and reads the resulting `quality_report.json`
   - Compares per-pillar grades against `grade_anchors.json` using the existing `_within_band` tolerance (±1 letter, GRADE_ORDER = D/C/B/A/S)
   - Prints a table: `run_key | pillar | anchor | actual | Δ | status`
   - Prints summary: `N pillars checked — K regressions found`
   - Exits 0 if no regressions, 1 if any regression, 2 on setup error
2. `--dry-run` mode: skip re-running the engine; read existing `data/calibration/{run_key}/quality_report.json` directly and diff against anchors. Useful for quick checks after calibration data is already fresh.
3. `--scenario` flag: allow running a single named scenario (e.g. `--scenario dungeon_crawl_seed42_200t`).
4. `make evaluate` Makefile target (fast scenarios only, using `--dry-run` by default to avoid expensive re-runs in CI-like usage; full engine run available via `make evaluate-full`).
5. Update `docs/simulation_quality/quality_scoring_contract.md` with a new §11.4 documenting the harness.
6. Add INFRA-252 to `docs/parity_ledger/infrastructure.yaml`.

## Out of Scope
- Integrating into any CI system (no `.github/workflows` changes)
- Slow (1000t+) scenarios in `make evaluate` — those remain in `make evaluate-full` or manual runs
- Changing the grade_anchors.json fixture or scoring weights
- The calibration corpus expansion (see TCK-20260702-SIMQ-EVAL-MATRIX — must be done first)

## Acceptance Criteria
1. `python3 tools/evaluate_simq.py --dry-run` reads existing calibration reports and prints a grade comparison table without error.
2. Output table has columns: `run_key`, `pillar`, `anchor`, `actual`, `status` (PASS / REGRESS / MISSING).
3. Exit code 0 when all pillars are within ±1 band, exit code 1 when any regression detected, exit code 2 on missing anchor file or invalid grade.
4. `python3 tools/evaluate_simq.py --dry-run --scenario dungeon_crawl_seed42_200t` runs only that scenario.
5. `make evaluate` exists in Makefile and calls `evaluate_simq.py --dry-run` successfully.
6. `make evaluate-full` exists in Makefile and calls `evaluate_simq.py` (with engine re-run) for fast scenarios.
7. `docs/simulation_quality/quality_scoring_contract.md` §11.4 documents the harness (invocation, dry-run vs full, exit codes, how to update anchors).
8. INFRA-252 added to `docs/parity_ledger/infrastructure.yaml` (status: verified, test_path pointing to evaluate_simq.py or a unit test).
9. At least 2 unit tests for `evaluate_simq.py` core logic (band comparison, table formatting or exit code logic) in `tests/simulation_quality/test_evaluate_harness.py`.

## Related Tickets
- TCK-20260702-SIMQ-EVAL-MATRIX (prerequisite) — must run first; expands the canonical scenario set that the harness covers
- TCK-20260630-SIMQ-ANCHORS (done) — established grade_anchors.json and _within_band logic
- TCK-20260701-SIMQ-LOOP-WINDOW-TUNE (done) — calibrate_simq.py is the engine this harness drives

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §11.3 (anchor update instructions; §11.4 to be added)
- `docs/parity_ledger/infrastructure.yaml` (add INFRA-252)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260630-SIMQ-ANCHORS/investigation.md` — _within_band logic and grade extraction patterns (reuse directly)

## Related Code Areas
- `tools/evaluate_simq.py` (new)
- `tools/calibrate_simq.py` (invoked by harness in full mode; read-only in dry-run mode)
- `Makefile` (new targets: `evaluate`, `evaluate-full`)
- `tests/simulation_quality/test_grade_regression.py` (reference: FAST_ANCHOR_KEYS list; not modified)
- `tests/simulation_quality/fixtures/grade_anchors.json` (read by harness)
- `tests/simulation_quality/test_evaluate_harness.py` (new unit tests)
- `docs/simulation_quality/quality_scoring_contract.md` (updated)
- `docs/parity_ledger/infrastructure.yaml` (updated)

## Assumptions / Open Questions
- The harness imports `calibrate_simq.main()` inline (not subprocess) so it runs in the same Python environment and avoids shell quoting issues with env flags. If ENABLE_ADVENTURE_ROUTING=ON is needed for simq_routing_test, the harness sets `os.environ["ENABLE_ADVENTURE_ROUTING"] = "ON"` before calling main and restores it after.
- `--dry-run` is the default for `make evaluate` because: (a) fast scenarios take ~25s × N runs, (b) the regression test already validates calibration data freshness, (c) re-running the full engine belongs in pre-release workflows, not routine checks.
- The harness should import `_within_band`, `_extract_pillar_grades`, `GRADE_ORDER` from `tests/simulation_quality/test_grade_regression.py` — OR duplicate the minimal logic (3 lines). Prefer duplication to avoid a `tests/` import in `tools/`. **Open:** confirm no existing `src/` utility for this.
- FAST_ANCHOR_KEYS is the canonical list for `make evaluate` at time of writing. After TCK-20260702-SIMQ-EVAL-MATRIX adds new keys, they should be incorporated into the harness's default scenario list.

## Implementation Notes

Created `tools/evaluate_simq.py` with 7 functions: `_within_band`, `_extract_pillar_grades`, `_parse_run_key` (regex `^(.+)_seed(\d+)_(\d+)t$`), `_load_calibration_report`, `_run_calibration` (patches sys.argv + env, calls calibrate_simq.main()), `_compare`, `_print_table`. `_within_band` and `_extract_pillar_grades` duplicated from test_grade_regression.py (not imported from tests/). `ROUTING_KEYS` set identifies the 3 simq_routing_test keys requiring ENABLE_ADVENTURE_ROUTING=ON. Default scenario list is all non-`_` keys from grade_anchors.json (25 entries). Smoke-test: 250 pillars checked — 0 regressions — 0 missing, exit 0.

`make evaluate` / `make evaluate-full` added to Makefile with new `PYTHON` variable using same env-detection pattern as `eval-search`. Both targets added to `.PHONY`. `§11.6` (not §11.4 — §11.4/11.5 were already taken by Performance/Scenario Coverage) added to quality_scoring_contract.md. INFRA-252 appended to infrastructure.yaml.

## Test Summary
`pytest tests/simulation_quality/test_evaluate_harness.py` — 17 tests pass (8 `TestWithinBand`, 5 `TestCompare`, 4 `TestParseRunKey`).
`pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` — 15 passed (unchanged).

## Files Changed
- `tools/evaluate_simq.py` (new)
- `Makefile` (updated — PYTHON var + evaluate/evaluate-full targets + .PHONY)
- `tests/simulation_quality/test_evaluate_harness.py` (new — 17 tests)
- `docs/simulation_quality/quality_scoring_contract.md` (updated — §11.6)
- `docs/parity_ledger/infrastructure.yaml` (updated — INFRA-252)

## Completion Summary
Created `tools/evaluate_simq.py` — standing SimQ quality gate that diffs calibration grades against all 25 `grade_anchors.json` entries using ±1 band tolerance. `--dry-run` reads existing data/calibration/ reports (no engine re-run); full mode patches sys.argv + env and calls calibrate_simq.main(). ROUTING_KEYS set gates ENABLE_ADVENTURE_ROUTING=ON for the 3 simq_routing_test scenarios. Smoke-test: 250 pillars checked, 0 regressions, exit 0. Added `make evaluate` (dry-run) and `make evaluate-full` (engine re-run for all 25 anchors) to Makefile with new PYTHON env-detection variable. 17 unit tests in test_evaluate_harness.py (all pass). §11.6 added to quality_scoring_contract.md; INFRA-252 added to infrastructure.yaml.
