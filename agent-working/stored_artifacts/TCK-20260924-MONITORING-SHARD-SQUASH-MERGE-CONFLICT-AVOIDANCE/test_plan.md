---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE
date: 2026-09-24
tags: [agent-monitoring, data-quality, process-improvement]
---

# Test Plan — TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE

`tests/tools/test_monitoring_consolidation.py`, one test per Acceptance Criterion (AC1, AC2, AC4,
AC5) as detailed in plan.md's Tests section, plus:

## Regression-prone paths
- `test_post_tool_hook_falls_back_to_shared_file_when_no_ticket_id`: the exact today-unchanged
  path for ad-hoc (non-ticket) work.
- `test_record_events_mixed_run_id_batch_splits_correctly`: a batch with two different `run_id`s
  writes to two separate per-ticket files, not one.
- `test_consolidation_leaves_per_ticket_file_in_place_on_failed_canonical_write`: a forced
  `write_lines` failure does not delete the source per-ticket file (idempotent-retry guarantee).
- `test_writer_py_unchanged`: source-diff assertion per plan.md item 5.
- `test_working_log_csv_writer_untouched`: `tests/tools/test_working_log_writer.py`'s own existing
  `test_working_log_csv_has_exactly_one_writer` guard still passes unchanged, confirming the
  disclosed scope reduction didn't accidentally touch that file.

## Full regression check
`pytest tests/tools/test_monitoring_consolidation.py tests/tools/test_record_run.py
tests/tools/test_record_events.py tests/tools/test_post_tool_hook.py
tests/tools/test_working_log_writer.py tests/tools/test_done_checker_static.py -v`, then
`pytest tests/tools/ -m "not slow"`.

## Recorded in `## Test Summary` once run
Exact commands and pass/fail counts.
