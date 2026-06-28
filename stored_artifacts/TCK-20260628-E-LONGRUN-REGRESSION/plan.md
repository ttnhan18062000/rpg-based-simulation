# Plan — TCK-20260628-E-LONGRUN-REGRESSION

## Ordered Steps

### Step 1 — Test harness (`tests/regression/test_behavioral_5k.py`)
- Create `tests/regression/__init__.py`
- `collect_behavioral_metrics(ticks, seed, world_id)`:
  - Load urban_political via WorldRepository + WorldCompiler
  - Enable ENABLE_ADVENTURE_ROUTING = 1.0
  - Run Kernel for 5000 ticks; call MetricsService.extract_metrics() every 100 ticks
  - Return alive_avg, gold_avg, quest_active_count
- `_check_metric(name, actual, baseline, threshold)` — relative drift comparison with
  absolute fallback when baseline=0.0
- `test_behavioral_5k_regression()` marked `@pytest.mark.extra_slow @pytest.mark.regression`
  — skips if baseline not found; compares actual vs baseline with THRESHOLDS

**Files changed:** `tests/regression/__init__.py`, `tests/regression/test_behavioral_5k.py`

### Step 2 — Baseline generator (`tools/generate_regression_baseline.py`)
- Calls `collect_behavioral_metrics()`, wraps result in versioned JSON with metadata
- Writes to `tests/regression/baseline_5k.json`

**Files changed:** `tools/generate_regression_baseline.py`

### Step 3 — Makefile target
- `regression-baseline:` calls `python3 tools/generate_regression_baseline.py`

**Files changed:** `Makefile`

### Step 4 — CI wiring
- Existing `slow` job already runs `pytest tests/ -m "slow or extra_slow"`.
  The `extra_slow` mark on `test_behavioral_5k_regression` routes it into this job.
- Update step name to acknowledge 5k regression explicitly.

**Files changed:** `.github/workflows/test.yml`

### Step 5 — Generate and commit baseline
- Run `make regression-baseline` to produce `tests/regression/baseline_5k.json`
- Commit the baseline file

**Files changed:** `tests/regression/baseline_5k.json`

## Scope Guards

- Do NOT modify kernel, scheduler, or domain logic.
- Do NOT add performance assertions (use cert tests for that).
- Do NOT run the full suite — scoped to `tests/regression/` and related.

## Dependency Map

Steps 1 → 2 → 3 → 4 are independent. Step 5 depends on Step 1.

## Acceptance Criteria Mapping

| AC | Steps |
|---|---|
| 5k-tick run < 10 minutes | Step 1 (harness), verified by Step 5 |
| Behavioral metrics captured + compared | Steps 1–2 |
| Named diagnostic on regression | Step 1 (_check_metric) |
| Baseline versioned artifact | Steps 2, 5 |
| CI slow job coverage | Step 4 |

## Deviations

- `activity_rate` metric not implemented as a separate metric (was in original scope assumptions).
  Replaced by `gold_avg` which directly captures economic activation — more stable and precise.
- Threshold for `gold_avg` set to ±20% (not specified in ticket) matching quest_active_count band.
