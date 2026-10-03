# Test Plan — TCK-20260701-SIMQ-LOOP-WINDOW-TUNE

## Regression Surface (existing tests that must pass)
- `tests/simulation_quality/test_accumulator.py` — all 10 tests; window_buffer cap and loop detection fire/no-fire tests are directly in scope
- `tests/simulation_quality/test_grade_regression.py` — grade anchors; must pass unchanged (no scoring weight changes in this ticket)
- `tests/simulation_quality/test_quality_hub_integration.py` — integration path

## New Tests Required (per AC)

### 1. CLI window-size override is run-scoped
File: `tests/simulation_quality/test_accumulator.py`

Test: `test_accumulator_respects_injected_window_size`
- Create a `DetectionParams`-patched `ScoringWeights` with `window_size=50`
- Add 100 events to a `PillarAccumulator(weights=patched_weights)`
- Assert `len(acc.window_buffer) <= 50` (not 200)
- This proves the override flows through without mutating the YAML

Test: `test_accumulator_respects_injected_loop_threshold`
- Create a `DetectionParams`-patched `ScoringWeights` with `loop_threshold=0.50`
- Add 60 events tagged "x" + 40 events tagged "y" (100 total, "x" = 60% of window)
- With default 0.70: loop should NOT fire. With 0.50: loop SHOULD fire.
- Assert "x" in `acc.loop_flags` when threshold=0.50

## Scoped Pytest Commands
```bash
# Primary: accumulator unit tests (directly changed behavior)
pytest tests/simulation_quality/test_accumulator.py -v

# Regression guard: grade anchors must not shift
pytest tests/simulation_quality/test_grade_regression.py -v

# Integration
pytest tests/simulation_quality/test_quality_hub_integration.py -v

# Full SimQ suite (excludes slow)
pytest tests/simulation_quality/ -m "not slow" -v
```

## Anti-Drift Test Guards
- `test_window_buffer_capped_at_maxlen`: already guards against window_size regression — must remain passing with both default and patched weights.
- `test_loop_detection_fires_above_threshold` and `test_loop_detection_does_not_fire_below_threshold`: explicitly parameterize threshold=0.70, so they remain stable regardless of YAML changes.
