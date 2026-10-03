---
ticket_id: TCK-20260614-OBS-BACKPRESSURE
date: 2026-06-14
---

# Test Plan: TCK-20260614-OBS-BACKPRESSURE

File: `tests/unit/observability/test_obs_backpressure.py`

| # | Test Class | Test | Coverage |
|---|-----------|------|----------|
| 1 | TestObservabilityMode | test_mode_enum_values | All 4 values correct |
| 2 | TestObservabilityMode | test_mode_is_str_enum | Inherits str |
| 3 | TestObservabilityController | test_normal_below_70pct | NORMAL at 0% and 69% |
| 4 | TestObservabilityController | test_pressure_at_70pct | PRESSURE at 70% |
| 5 | TestObservabilityController | test_pressure_between_70_and_90 | PRESSURE at 85% |
| 6 | TestObservabilityController | test_degraded_at_90pct | DEGRADED at 90% |
| 7 | TestObservabilityController | test_degraded_between_90_and_100 | DEGRADED at 95% |
| 8 | TestObservabilityController | test_survival_at_100pct | SURVIVAL at 100% |
| 9 | TestObservabilityController | test_survival_above_100pct | SURVIVAL above 100% |
| 10 | TestObservabilityController | test_evaluate_ignores_event_rate | event_rate irrelevant |
| 11 | TestNormalMode | test_normal_mode_records_all_events | All 5 severities recorded |
| 12 | TestNormalMode | test_normal_mode_does_not_drop | No drops at 50% fill |
| 13 | TestPressureMode | test_pressure_mode_samples_info_events | 2 of 10 INFO pass |
| 14 | TestPressureMode | test_pressure_mode_keeps_warning_events | WARNING always passes |
| 15 | TestPressureMode | test_pressure_mode_keeps_error_events | ERROR always passes |
| 16 | TestPressureMode | test_pressure_mode_increments_drop_count | 4 dropped of 4 sent |
| 17 | TestDegradedMode | test_degraded_mode_drops_info_events | INFO/DEBUG dropped |
| 18 | TestDegradedMode | test_degraded_mode_keeps_warning_events | WARNING passes |
| 19 | TestDegradedMode | test_degraded_mode_keeps_critical_events | CRITICAL passes |
| 20 | TestSurvivalMode | test_survival_mode_no_queue_enqueue | Zero queue pushes |
| 21 | TestSurvivalMode | test_survival_mode_no_buffer_append | Zero buffer appends |
| 22 | TestSurvivalMode | test_survival_mode_increments_counters | Per-type counters |
| 23 | TestSurvivalMode | test_survival_mode_counts_all_severities | All severities counted |
| 24 | TestObservabilityStatus | test_status_initial_state | Mode/drops/counts shape |
| 25 | TestObservabilityStatus | test_status_reflects_current_mode | Mode field correct |
| 26 | TestObservabilityStatus | test_status_events_dropped_accumulates | Drop count accurate |
| 27 | TestObservabilityStatus | test_status_survival_counts_exposed | survival_counts dict |
| 28 | TestResetMode | test_reset_mode_clears_state | All fields cleared |

Run: `pytest tests/unit/observability/test_obs_backpressure.py -v`
