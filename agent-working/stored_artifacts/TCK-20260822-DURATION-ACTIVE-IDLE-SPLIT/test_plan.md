# Test Plan — TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT

## New tests
- `tests/tools/test_duration_utils.py` (new file):
  - `test_all_active_when_no_gap_exceeds_threshold`
  - `test_single_large_gap_is_fully_idle`
  - `test_no_events_treats_entire_span_by_threshold`
  - `test_seq_collision_orders_by_ts_not_seq`
  - `test_events_with_missing_or_non_string_ts_are_skipped`
  - `test_unparseable_start_or_end_ts_returns_none`
  - `test_active_plus_idle_equals_total_duration_invariant`
  - `test_real_corpus_simq_depth_social_reproduces_documented_gap` (AC5)
  - `test_largest_gap_boundary_labels_identify_correct_phase_transition`

## Updated tests
- `tests/tools/test_retrieval_baseline_metrics.py`:
  - `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists` →
    rewritten for real gap-aware output shape.
  - `test_baseline_report_would_prefer_gap_aware_view_if_available` → retired, replaced with
    `test_baseline_report_duration_section_uses_duration_utils_when_available`.
- `tests/tools/test_generate_retro.py`: add assertions covering the new Slow Runs / Duration
  outliers columns and the idle-dominated-run disclaimer line.

## Scoped pytest commands
```
pytest tests/tools/test_duration_utils.py -q
pytest tests/tools/test_retrieval_baseline_metrics.py -q
pytest tests/tools/test_generate_retro.py -q
```
