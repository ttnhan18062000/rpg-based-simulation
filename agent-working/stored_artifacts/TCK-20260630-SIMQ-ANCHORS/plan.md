# Plan — TCK-20260630-SIMQ-ANCHORS

## Summary

Rewrite `tests/simulation_quality/test_grade_regression.py` to use empirical grades from
committed calibration reports as regression anchors. Replace the old "UNKNOWN" stub fixture
and the old simulation-re-running approach with a parametric band-tolerance check against
`data/calibration/{run_key}/quality_report.json`.

## Steps

### 1. Write tests/simulation_quality/fixtures/grade_anchors.json

Format: `{run_key: {PILLAR: GRADE, ...}, ...}` for 8 run keys (6 fast + 2 slow).
Grades taken from `data/calibration/{run_key}/quality_report.json` (authoritative source).

### 2. Rewrite tests/simulation_quality/test_grade_regression.py

Complete rewrite. Old stub approach (import run_and_grade, actually re-run sim) is replaced
with static comparison against existing calibration reports.

Key design choices:
- `GRADE_ORDER = ["D", "C", "B", "A", "S"]` (ascending quality, 5 grades)
- `_within_band(actual, anchor, tolerance=1)` using index distance
- Module-scoped `grade_anchors` fixture loading the JSON file
- `FAST_ANCHOR_KEYS` (6 run keys, 200t/500t) — parametrize without slow mark
- `SLOW_ANCHOR_KEYS` (2 run keys, 1000t) — parametrize with `@pytest.mark.slow`
- `_extract_pillar_grades(report)` reads `report["pillars"][pillar]["grade"]`
- Calibration report path: `data/calibration/{run_key}/quality_report.json` (relative to repo root)
- Tests skip if calibration file missing (forward-compatible)
- `test_grade_anchor_file_exists_and_valid` updated to new fixture schema

### 3. Run fast tests to verify pass

```bash
pytest tests/simulation_quality/test_grade_regression.py -v -m "not slow"
```

### 4. Mutation test

Temporarily set one anchor to wildly wrong grade → confirm test fails → restore.

### 5. Update parity ledger INFRA-250

The entry records "4 skipped: 2 grade regression anchors UNKNOWN" — update test_path and
v2_evidence to reflect populated anchors and new parametric test structure.

## Architecture constraints

- Tests read calibration reports (static files). No engine runs, no durable state mutation.
- `data/calibration/` is authoritative source; `grade_anchors.json` is the committed snapshot.
- Tests are idempotent and deterministic.
- No new imports from src/ (pure stdlib + pytest).
