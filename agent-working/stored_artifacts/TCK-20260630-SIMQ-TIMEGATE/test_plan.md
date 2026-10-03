# Test Plan — TCK-20260630-SIMQ-TIMEGATE

## Objective

Create `tests/simulation_quality/test_timegate_penalties.py` with consolidated per-pillar
time-gate unit tests discoverable by `pytest -k timegate`. All tests inject events directly
into scorer instances (no full engine run). Calibration runs are @pytest.mark.slow.

## Test File: tests/simulation_quality/test_timegate_penalties.py

### Pattern

For each pillar + gate:
1. Create a fresh scorer instance
2. Build a ScoringContext with controlled tick value and empty/zero window_tag_counts
3. Feed a triggering event envelope
4. Assert penalty fires at `threshold + 1` (tag in record.tags, delta == expected weight)
5. Assert penalty does NOT fire at `threshold - 1` (tag absent or record is positive)
6. Assert penalty fires only once (second call after first fire returns different tags)

### Classes and Tests

#### TestEconomyTimegate
- `test_zero_harvest_timegate_fires_at_threshold` — tick=100+1, no harvest_active in window → zero_harvest tag, delta==weights["zero_harvest"]
- `test_zero_harvest_timegate_not_before_threshold` — tick=100-1, no harvest_active → harvest_active tag (positive signal, no gate)
- `test_zero_harvest_timegate_fires_once` — second resource_harvested call after gate fires → no zero_harvest tag
- `test_zero_crafting_timegate_fires_at_threshold` — tick=200+1, no crafting_active → zero_crafting tag
- `test_zero_crafting_timegate_not_before_threshold` — tick=200-1 → crafting_active tag (no gate)
- `test_zero_crafting_timegate_fires_once` — fires once
- `test_zero_trade_timegate_fires_at_threshold` — tick=300+1, no trade_active → zero_trade tag
- `test_zero_trade_timegate_not_before_threshold` — tick=300-1 → trade_active tag (no gate)
- `test_zero_trade_timegate_fires_once` — fires once

#### TestProgressionTimegate
- `test_all_level_1_timegate_fires_at_threshold` — tick=200+1, no level_milestone in window → all_level_1 tag
- `test_all_level_1_timegate_not_before_threshold` — tick=200-1, no level_milestone → level_milestone tag (positive)
- `test_all_level_1_timegate_fires_once` — fires once
- `test_progression_frozen_fires_on_xp_freeze_payload` — progression_plateau_detected (type=xp_freeze) → progression_frozen tag, delta<0 (not tick-gated in scorer, engine-side detection)
- `test_xp_plateau_timegate_fires_at_threshold` — tick=50+1, progression_plateau_detected (type=xp_rate_zero) → xp_plateau tag
- `test_xp_plateau_timegate_not_before_threshold` — tick=50-1 → None (gate not met, no match returns None)

#### TestNarrativeTimegate
- `test_quest_dormant_timegate_fires_at_threshold` — tick=200+1, no quest_active → quest_system_dormant tag
- `test_quest_dormant_timegate_not_before_threshold` — tick=200-1, no quest_active → quest_active tag (positive)
- `test_quest_dormant_timegate_fires_once` — fires once
- `test_chronicle_silent_timegate_fires_at_threshold` — tick=300+1, no narrative_event in window → history_silent tag
- `test_chronicle_silent_timegate_not_before_threshold` — tick=300-1 → history_forming tag (positive)
- `test_chronicle_silent_timegate_fires_once` — fires once

#### TestAgencyTimegate
- `test_stasis_N_timegate_fires_after_gate` — defer_idle count = stasis_gate+3, tick=100 → stasis_N tag, delta includes stasis_per_tick*3
- `test_stasis_N_timegate_not_before_gate` — defer_idle count = stasis_gate-1 → stasis_N absent
- `test_stasis_N_timegate_accumulates_linearly` — defer_idle=gate+N, assert delta == base + stasis_per_tick*N
- `test_population_stasis_timegate_fires_at_gate` — tick=stasis_gate+1, action_taken=0, defer_idle>0 → population_stasis tag
- `test_population_stasis_timegate_not_before_gate` — tick=stasis_gate-1 → no population_stasis tag
- `test_population_stasis_timegate_fires_once` — fires once

## Marks

- Fast tests (inject events): no mark — run in default suite
- `@pytest.mark.slow`: only for any test that requires an actual engine calibration run
  - All tests in this file are fast (event injection only), so NO slow marks in this file
  - The 1000-tick calibrations are NOT run as pytest tests — they run via calibrate_simq.py directly

## Execution Targets

```bash
# Primary: all timegate tests
pytest tests/simulation_quality/test_timegate_penalties.py -v --timeout=60

# Acceptance criterion
pytest tests/simulation_quality/ -k timegate -v

# Full SimQ suite (non-slow)
pytest tests/simulation_quality/ -v --timeout=120 -m "not slow"
```

## Expected Result

All tests in `test_timegate_penalties.py` pass. Count: ~24 tests.
