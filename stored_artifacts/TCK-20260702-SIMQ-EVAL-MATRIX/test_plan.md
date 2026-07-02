# TCK-20260702-SIMQ-EVAL-MATRIX — Test Plan

**Date:** 2026-07-02
**Ticket:** TCK-20260702-SIMQ-EVAL-MATRIX
**Phase:** Investigation (seq 2)

---

## 1. Regression Surface

`tests/simulation_quality/test_grade_regression.py` is the single test file governing all grade anchor checks. It must pass before AND after this ticket's changes.

### Baseline verification (before any changes)

Run to confirm pre-condition green:

```bash
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v
pytest tests/simulation_quality/test_grade_regression.py -m slow -v
```

Expected: all 6 fast parametrize entries pass, both slow entries pass. No new failures must be introduced. If any baseline test is already failing, that is a blocking pre-condition — stop and investigate before proceeding.

### Post-change verification

After calibration runs complete and grade_anchors.json is updated:

```bash
# Fast suite only (CI gate — runs in seconds, no calibration data needed for new skips)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Full suite including new slow keys
pytest tests/simulation_quality/test_grade_regression.py -v
```

All parametrize entries that have calibration data AND grade_anchors.json entries must pass. Entries without calibration data auto-skip (this is safe for intermediate states).

---

## 2. New Tests Required

### 2a. New FAST_ANCHOR_KEYS entries

Add the following 8 run_keys to `FAST_ANCHOR_KEYS` in `test_grade_regression.py`:

```python
FAST_ANCHOR_KEYS = [
    # existing
    "sandbox_world_seed42_200t",
    "sandbox_world_seed137_200t",
    "sandbox_world_seed999_200t",
    "dungeon_crawl_seed42_200t",
    "urban_political_seed42_200t",
    "simq_routing_test_seed42_500t",
    # new — simq_routing_test additional seeds
    "simq_routing_test_seed123_500t",
    "simq_routing_test_seed456_500t",
    # new — dungeon_crawl 500t
    "dungeon_crawl_seed42_500t",
    "dungeon_crawl_seed123_500t",
    "dungeon_crawl_seed456_500t",
    # new — urban_political 500t
    "urban_political_seed42_500t",
    "urban_political_seed123_500t",
    "urban_political_seed456_500t",
]
```

These are covered by the existing `test_grade_within_anchor_band` parametrize — no new test function needed.

### 2b. New SLOW_ANCHOR_KEYS entries

Add the following 9 run_keys to `SLOW_ANCHOR_KEYS` in `test_grade_regression.py`:

```python
SLOW_ANCHOR_KEYS = [
    # existing
    "dungeon_crawl_seed42_1000t",
    "sandbox_world_seed42_1000t",
    # new — dungeon_crawl 1000t
    "dungeon_crawl_seed123_1000t",
    "dungeon_crawl_seed456_1000t",
    # new — urban_political 1000t
    "urban_political_seed42_1000t",
    "urban_political_seed123_1000t",
    "urban_political_seed456_1000t",
    # new — dungeon_crawl 2000t
    "dungeon_crawl_seed42_2000t",
    "dungeon_crawl_seed123_2000t",
    "dungeon_crawl_seed456_2000t",
    # new — sandbox_world 2000t
    "sandbox_world_seed42_2000t",
]
```

These are covered by the existing `test_grade_within_anchor_band_long_run` parametrize — no new test function needed.

### 2c. AGENCY-specific spot check (not a code change — manual verification step)

After calibration runs for `simq_routing_test` seeds 123 and 456, verify acceptance criterion 6:

```bash
python3 -c "
import json, pathlib
for seed in [123, 456]:
    key = f'simq_routing_test_seed{seed}_500t'
    p = pathlib.Path(f'data/calibration/{key}/quality_report.json')
    if p.exists():
        grades = json.loads(p.read_text())['pillars']
        agency = grades['AGENCY']['grade']
        status = 'PASS' if agency in ('B', 'A', 'S') else 'FAIL'
        print(f'{key}: AGENCY={agency} [{status}]')
    else:
        print(f'{key}: NOT FOUND')
"
```

Expected output: AGENCY=B (or better) for both seeds.

### 2d. grade_anchors.json entries required

For each of the 17 new run_keys, add an entry to `tests/simulation_quality/fixtures/grade_anchors.json` with empirical grades extracted from the calibration report:

```python
# Extraction script (run once per run_key after calibration completes)
python3 -c "
import json, pathlib, sys
run_key = sys.argv[1]
p = pathlib.Path(f'data/calibration/{run_key}/quality_report.json')
report = json.loads(p.read_text())
grades = {k: v['grade'] for k, v in report['pillars'].items()}
print(json.dumps({run_key: grades}, indent=2))
" <run_key>
```

The JSON output is pasted into grade_anchors.json. Repeat for all 17 new keys. No anchor values should be guessed or interpolated.

---

## 3. Scoped Pytest Commands

### Pre-calibration baseline (run before any code or fixture changes)

```bash
# Fast suite: must pass before changes
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Slow suite: must pass before changes
pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Structural sanity (verifies fixture schema):
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v
```

### During calibration (intermediate state — list additions without data yet)

After adding new keys to FAST/SLOW lists and grade_anchors.json but before calibration completes, new parametrize entries will auto-skip. This is expected:

```bash
# Fast-only: see skips for new keys (expected), passes for existing keys
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Structural sanity will FAIL here if grade_anchors.json is not yet populated for new fast keys
# Therefore: do NOT expand FAST_ANCHOR_KEYS until grade_anchors.json entries exist
```

### Post-calibration final verification

```bash
# Full fast suite: all 14 fast keys must pass (no skips for fast keys)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v

# Full slow suite: all 11 slow keys must pass (no skips for slow keys)
pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Full combined (authoritative green gate for this ticket)
pytest tests/simulation_quality/test_grade_regression.py -v

# Structural sanity check
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v
```

### AGENCY spot-check command (acceptance criterion 6)

```bash
pytest tests/simulation_quality/test_grade_regression.py \
  -k "simq_routing_test_seed123 or simq_routing_test_seed456" -v -m "not slow"
```

Both must pass (not skip) and show no band drift for AGENCY.

---

## 4. Anti-Drift Test Guards

### Guard G1 — Do not commit anchor entries before calibration data exists

The test auto-skips when `data/calibration/{run_key}/quality_report.json` is absent. A committed grade_anchors.json entry for a non-existent calibration report will NOT cause a test failure but WILL cause the structural sanity test to expect it. Pattern: calibration data and grade_anchors.json entry are committed together in the same commit.

### Guard G2 — MINIMUM_FAST_ANCHORS enforcement

`test_grade_anchor_file_exists_and_valid` asserts that every key in `FAST_ANCHOR_KEYS` exists in grade_anchors.json with 10 valid pillar grades. After expansion:

```bash
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v
```

This must be run after every FAST_ANCHOR_KEYS addition. If it fails, grade_anchors.json is missing entries for the new fast keys.

### Guard G3 — Band tolerance is ±1 letter, not exact match

The test uses `_within_band(actual, anchor, tolerance=1)`. This means an anchor of B accepts A, B, or C. When setting anchors empirically, set them to the actual grade from the calibration run — do not set anchors one level lower than actual to "leave room." Setting an anchor to C when actual is B would accept D as passing, which is incorrect.

### Guard G4 — Slow test marker must be present on slow tests

`test_grade_within_anchor_band_long_run` carries `@pytest.mark.slow`. All 1000t and 2000t run_keys are in `SLOW_ANCHOR_KEYS` and are covered by this function. Do not add 1000t/2000t keys to `FAST_ANCHOR_KEYS` — they would run in the standard fast suite and slow down CI unnecessarily.

### Guard G5 — Verify calibration report integrity before extracting grades

Before populating grade_anchors.json from a new calibration run, verify the report is complete:

```bash
python3 -c "
import json, pathlib
for key in [
    'simq_routing_test_seed123_500t',
    'simq_routing_test_seed456_500t',
    'dungeon_crawl_seed42_500t',
    'dungeon_crawl_seed123_500t',
    'dungeon_crawl_seed456_500t',
    'urban_political_seed42_500t',
    'urban_political_seed123_500t',
    'urban_political_seed456_500t',
    'dungeon_crawl_seed123_1000t',
    'dungeon_crawl_seed456_1000t',
    'urban_political_seed42_1000t',
    'urban_political_seed123_1000t',
    'urban_political_seed456_1000t',
    'dungeon_crawl_seed42_2000t',
    'dungeon_crawl_seed123_2000t',
    'dungeon_crawl_seed456_2000t',
    'sandbox_world_seed42_2000t',
]:
    p = pathlib.Path(f'data/calibration/{key}/quality_report.json')
    if not p.exists():
        print(f'MISSING: {key}')
        continue
    r = json.loads(p.read_text())
    pillars = r.get('pillars', {})
    ticks = r.get('run_metadata', {}).get('ticks', '?')
    print(f'OK ({ticks}t, {len(pillars)} pillars): {key}')
"
```

Expected: all 17 lines show `OK` with correct tick counts and 10 pillars.

### Guard G6 — ENABLE_ADVENTURE_ROUTING flag verification for simq_routing_test runs

Before accepting simq_routing_test calibration reports as valid, verify the flag was active:

```bash
python3 -c "
import json, pathlib
for seed in [42, 123, 456]:
    key = f'simq_routing_test_seed{seed}_500t'
    p = pathlib.Path(f'data/calibration/{key}/quality_report.json')
    if p.exists():
        r = json.loads(p.read_text())
        agency = r['pillars'].get('AGENCY', {}).get('grade', '?')
        print(f'{key}: AGENCY={agency} (expected B or better)')
"
```

If AGENCY=C for any seed, the ENABLE_ADVENTURE_ROUTING flag was not active for that run. Rerun with the flag explicitly set.
