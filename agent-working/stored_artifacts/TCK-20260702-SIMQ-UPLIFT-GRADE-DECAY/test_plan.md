# Test Plan: TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY

**Date:** 2026-07-02  
**Decision:** D2 — Fix tick-dilution artifact via last_event_tick divisor cap  
**Scope:** Accumulator, report builder, grade regression, anchor update

---

## 1. Unit Tests — PillarAccumulator

**File:** `tests/simulation_quality/test_pillar_accumulator.py`

### T-ACC-01: `last_event_tick` is zero on construction

```python
def test_last_event_tick_zero_on_init():
    acc = PillarAccumulator(PillarId.COMBAT)
    snap = acc.snapshot()
    assert snap["last_event_tick"] == 0
```

### T-ACC-02: `last_event_tick` advances to the tick of the first event

```python
def test_last_event_tick_set_on_first_add():
    acc = PillarAccumulator(PillarId.COMBAT)
    rec = make_score_record(tick=42)
    acc.add(rec)
    assert acc.snapshot()["last_event_tick"] == 42
```

### T-ACC-03: `last_event_tick` takes the maximum across multiple events

```python
def test_last_event_tick_is_max():
    acc = PillarAccumulator(PillarId.COMBAT)
    acc.add(make_score_record(tick=10))
    acc.add(make_score_record(tick=50))
    acc.add(make_score_record(tick=30))
    assert acc.snapshot()["last_event_tick"] == 50
```

### T-ACC-04: Duplicate event_id does not advance `last_event_tick`

```python
def test_last_event_tick_not_updated_by_duplicate():
    acc = PillarAccumulator(PillarId.COMBAT)
    rec = make_score_record(tick=10, event_id="dup")
    acc.add(rec)
    # Add the same event again with a higher tick in the record — same event_id
    rec_dup = make_score_record(tick=999, event_id="dup")
    acc.add(rec_dup)
    assert acc.snapshot()["last_event_tick"] == 10
```

### T-ACC-05: `last_event_tick` appears in snapshot

```python
def test_last_event_tick_in_snapshot():
    acc = PillarAccumulator(PillarId.COMBAT)
    acc.add(make_score_record(tick=77))
    snap = acc.snapshot()
    assert "last_event_tick" in snap
    assert snap["last_event_tick"] == 77
```

---

## 2. Unit Tests — QualityReportBuilder (normalized_score formula)

**File:** `tests/simulation_quality/test_quality_report.py`

### T-REP-01: Normalized score uses last_event_tick when events exist (core fix assertion)

```python
def test_normalized_score_uses_last_event_tick_not_current_tick():
    """
    Same raw_score at 200 ticks and 401 ticks must produce the same normalized_score
    when last_event_tick is identical in both runs.
    """
    # Build two accumulators with identical events, but report them at different current_ticks
    acc_200 = make_accumulator_with_events(events_up_to_tick=172, raw_score=127.0)
    acc_401 = make_accumulator_with_events(events_up_to_tick=172, raw_score=127.0)

    report_200 = QualityReportBuilder.build(
        {PillarId.COMBAT: acc_200}, current_tick=200, run_id="r200", weights=make_weights()
    )
    report_401 = QualityReportBuilder.build(
        {PillarId.COMBAT: acc_401}, current_tick=401, run_id="r401", weights=make_weights()
    )

    norm_200 = report_200.pillars["COMBAT"].normalized_score
    norm_401 = report_401.pillars["COMBAT"].normalized_score

    # Both should divide by last_event_tick=172, not by 200 and 401
    assert abs(norm_200 - norm_401) < 0.001, (
        f"Same raw_score at different tick counts produced different normalized scores: "
        f"{norm_200:.4f} vs {norm_401:.4f}"
    )
```

### T-REP-02: Grade is identical for same activity regardless of run length

```python
def test_grade_stable_across_tick_counts_for_same_activity():
    """H2 regression: same combat events must not produce different grades at 200t vs 401t."""
    acc_200 = make_accumulator_with_events(events_up_to_tick=172, raw_score=127.0)
    acc_401 = make_accumulator_with_events(events_up_to_tick=172, raw_score=127.0)

    report_200 = QualityReportBuilder.build(
        {PillarId.COMBAT: acc_200}, current_tick=200, run_id="r200", weights=make_weights()
    )
    report_401 = QualityReportBuilder.build(
        {PillarId.COMBAT: acc_401}, current_tick=401, run_id="r401", weights=make_weights()
    )

    assert report_200.pillars["COMBAT"].grade == report_401.pillars["COMBAT"].grade, (
        "Grade must not change between 200t and 401t for identical activity"
    )
```

### T-REP-03: Zero-event pillar falls back to current_tick (existing behavior preserved)

```python
def test_zero_event_pillar_uses_current_tick_fallback():
    """Pillars with no events: last_event_tick=0 → fallback to current_tick.
    normalized_score = 0.0 / current_tick = 0.0 regardless, grade stays C."""
    acc = PillarAccumulator(PillarId.AGENCY)  # no events added

    report = QualityReportBuilder.build(
        {PillarId.AGENCY: acc}, current_tick=200, run_id="r", weights=make_weights()
    )
    snap = report.pillars["AGENCY"]
    assert snap.raw_score == 0.0
    assert snap.normalized_score == 0.0
    assert snap.grade == "C"
```

### T-REP-04: Normalized score = raw_score / last_event_tick (exact value check)

```python
def test_normalized_score_exact_calculation():
    """Unit check: raw=127.0, last_event_tick=172 → normalized = 127.0/172 = 0.7384..."""
    acc = make_accumulator_with_events(events_up_to_tick=172, raw_score=127.0)
    report = QualityReportBuilder.build(
        {PillarId.COMBAT: acc}, current_tick=500, run_id="r", weights=make_weights()
    )
    expected = 127.0 / 172
    assert abs(report.pillars["COMBAT"].normalized_score - expected) < 0.0001
```

### T-REP-05: Active-throughout scenario — last_event_tick ≈ current_tick, behavior unchanged

```python
def test_active_throughout_run_not_affected():
    """When events fire up to near current_tick, last_event_tick ≈ current_tick.
    Fix does not inflate scores for genuinely active runs."""
    # Simulate 200 events up to tick 199 (active throughout)
    acc = make_accumulator_with_events(events_up_to_tick=199, raw_score=100.0)
    report = QualityReportBuilder.build(
        {PillarId.COMBAT: acc}, current_tick=200, run_id="r", weights=make_weights()
    )
    # normalized = 100.0 / 199 ≈ 0.5025 → A (just above 0.5)
    expected = 100.0 / 199
    assert abs(report.pillars["COMBAT"].normalized_score - expected) < 0.001
```

---

## 3. Regression Tests — Grade Stability (cross-tick)

**File:** `tests/simulation_quality/test_grade_regression.py`

### T-REG-01: dungeon_crawl COMBAT grade matches A at 200t and 500t after fix

```python
def test_combat_grade_stable_across_tick_counts():
    """
    Reads grade_anchors.json. After D2 fix, COMBAT must be A at both 200t and 500t
    for dungeon_crawl_seed42.
    This test will FAIL under the old formula and PASS under the D2 fix.
    """
    anchors = load_grade_anchors()
    assert anchors["dungeon_crawl_seed42_200t"]["COMBAT"] == "A"
    assert anchors["dungeon_crawl_seed42_500t"]["COMBAT"] == "A"
    assert anchors["dungeon_crawl_seed123_500t"]["COMBAT"] == "A"
```

### T-REG-02: `make evaluate --dry-run` exits 0 after anchor update

This is a manual verification step, not a pytest test. Documented here as a required gate:

```bash
make evaluate
# Expected exit code: 0 (all PASS)
# If any REGRESS rows appear: anchor was not updated correctly
```

---

## 4. Quality Scores JSONL Diagnostic (manual / one-time)

These are the diagnostic checks that confirmed H2. They are documented here as reproducible evidence, not automated tests.

### D-01: Confirm zero COMBAT events after tick 200 in the 500t run

```python
python3 -c "
import json
from pathlib import Path
scores = Path('data/calibration/dungeon_crawl_seed42_500t/quality_scores.jsonl')
after = [json.loads(l) for l in scores.read_text().splitlines()
         if json.loads(l).get('pillar')=='COMBAT' and json.loads(l).get('tick',0)>200]
print(f'COMBAT events after tick 200: {len(after)}')
"
# Expected output: 'COMBAT events after tick 200: 0'
```

### D-02: Confirm raw_score is identical at 200t and 500t

```python
python3 -c "
import json
from pathlib import Path
for key in ['dungeon_crawl_seed42_200t','dungeon_crawl_seed42_500t']:
    r = json.loads(Path(f'data/calibration/{key}/quality_report.json').read_text())
    c = r['pillars']['COMBAT']
    print(f'{key}: raw={c[\"raw_score\"]} event_count={c[\"event_count\"]}')
"
# Expected output:
# dungeon_crawl_seed42_200t: raw=127.0 event_count=65
# dungeon_crawl_seed42_500t: raw=127.0 event_count=65
```

---

## 5. Parity Ledger Test Coverage

After adding the new `COMB-NNN` entry to `docs/parity_ledger/combat_movement.yaml`, the `test_path` must resolve:

```
tests/simulation_quality/test_grade_regression.py::test_combat_grade_stable_across_tick_counts
```

This is satisfied by T-REG-01 above.

---

## 6. Anchor Update Workflow (post-implementation)

1. Implement phases 1-2 (accumulator + report builder)
2. Run calibration:
   ```bash
   for seed in 42 123 456; do
     for ticks in 500 1000 2000; do
       python3 tools/calibrate_simq.py --name dungeon_crawl --seed $seed --ticks $ticks
     done
   done
   ```
3. Inspect `data/calibration/dungeon_crawl_seed*_{500,1000,2000}t/quality_report.json` for COMBAT grade
4. Expected: COMBAT grade = A (was B before fix)
5. Update `tests/simulation_quality/fixtures/grade_anchors.json` for all 9 affected entries
6. Run `make evaluate` → must exit 0
7. Commit calibration data, fixture, and doc updates together

---

## 7. Out-of-Scope Tests

- WORLD grade at 500t (stays B after fix — `last_event_tick ≈ 400`, normalized ≈ 0.44 < 0.5)
- Any scorer logic (no scorer changes in D2)
- COMBAT scoring weights (unchanged)
- Scenarios other than dungeon_crawl where COMBAT/WORLD events fire throughout the run (unaffected by fix)
