# Plan — TCK-20260702-SIMQ-EVAL-HARNESS

## Ordered Steps

### Step 1 — Create `tools/evaluate_simq.py`

New script. Functions:
- `GRADE_ORDER`, `ROUTING_KEYS` constants
- `_within_band(actual, anchor, tolerance=1) -> bool` — duplicated from test_grade_regression.py
- `_extract_pillar_grades(report) -> dict[str, str]`
- `_parse_run_key(run_key) -> tuple[str, int, int]` — regex `^(.+)_seed(\d+)_(\d+)t$`
- `_load_calibration_report(run_key) -> dict | None`
- `_run_calibration(name, seed, ticks, routing_flag)` — patches sys.argv, sets env var, calls calibrate_simq.main(), restores both
- `_compare(run_key, actual_grades, anchor_grades) -> list[dict]` — status: PASS/REGRESS/MISSING
- `_print_table(rows)` — aligned columns: run_key(40), pillar(12), anchor(7), actual(7), status(8)
- `main()` — argparse: --dry-run, --scenario, --anchors. Exit 0=all pass, 1=regress, 2=setup error.

Files: `tools/evaluate_simq.py` (new)

### Step 2 — Create `tests/simulation_quality/test_evaluate_harness.py`

Unit tests (≥9 tests):
- `test_within_band_same_grade`, `test_within_band_adjacent_pass`, `test_within_band_two_apart_fail`, `test_within_band_boundary`
- `test_compare_detects_regression`, `test_compare_passes_within_band`, `test_compare_missing_pillar`
- `test_parse_run_key_standard`, `test_parse_run_key_multiword`

Import: `sys.path.insert(0, '.')` then `from tools.evaluate_simq import _within_band, _compare, _parse_run_key`

Files: `tests/simulation_quality/test_evaluate_harness.py` (new)

### Step 3 — Add Makefile targets

Check if `PYTHON` variable already exists in Makefile. If not, define it. Add after `eval-search` target:
```makefile
evaluate: ## Diff current calibration data against grade anchors (no engine re-run)
	$(PYTHON) tools/evaluate_simq.py --dry-run

evaluate-full: ## Re-run engine for all fast (≤500t) scenarios and diff against grade anchors
	$(PYTHON) tools/evaluate_simq.py
```

Files: `Makefile`

### Step 4 — Update `docs/simulation_quality/quality_scoring_contract.md`

Add §11.4 after existing §11.3 (anchor update instructions):
Document `make evaluate` (dry-run), `make evaluate-full` (engine re-run for 14 fast scenarios), `--scenario` flag, output format, exit codes, and anchor update workflow.

Files: `docs/simulation_quality/quality_scoring_contract.md`

### Step 5 — Add INFRA-252 to `docs/parity_ledger/infrastructure.yaml`

Append after INFRA-251.

Files: `docs/parity_ledger/infrastructure.yaml`

### Step 6 — Run tests

```bash
pytest tests/simulation_quality/test_evaluate_harness.py -v
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v
```

### Step 7 — Smoke-test the harness

```bash
python3 tools/evaluate_simq.py --dry-run
```
Verify: table prints, exits 0, no REGRESS rows.

### Step 8 — Update ticket Implementation Notes and Files Changed

## Scope Guards
- No imports from `tests/` in `tools/evaluate_simq.py`
- No slow (≥1000t) scenarios in `make evaluate-full`
- Do not modify `calibrate_simq.py`, `grade_anchors.json`, or calibration data
- Check for existing `PYTHON` var in Makefile before redefining

## Dependency Map
- Step 1 → Step 2 (tests import from the script)
- Steps 1+2 → Step 6
- Steps 1+3 → Step 7
- Steps 4+5 are independent of 2, do alongside

## AC Mapping
- AC1,2,3,4: Step 1 + Step 7
- AC5: Step 3 (`make evaluate`)
- AC6: Step 3 (`make evaluate-full`)
- AC7: Step 4 (§11.4)
- AC8: Step 5 (INFRA-252)
- AC9: Step 2 + Step 6 (unit tests)

## Deviations
_(fill in if any step differs from plan during implementation)_
