# Test Plan — TCK-20260915-MONITORING-INTEGRITY-BACKLOG

- `tests/tools/test_validate_agent_monitoring.py`: new `_run_effective_start_ts` unit tests
  (field-priority, legacy-name fallback, None cases) plus a `TestNoEventsLegacyExclusion` class
  covering: pre-cutoff no-events run excluded (gate passes), at/after-cutoff no-events run still
  errors, unknown-start-ts run still errors (conservative default), legacy `ts`-field run before
  cutoff also excluded.
- `tests/tools/test_working_log_writer.py`: new `test_comma_bearing_title_round_trips` — a real
  comma-bearing title (mirroring the actual defect found) written via `append_working_log_row`
  round-trips exactly through `parse_working_log`.
- `tests/tools/test_monitoring_integrity_backlog_check.py` (new file): per-function unit tests for
  `find_working_log_rows_missing_run_record`, `find_unusable_ts_records`,
  `count_unknown_week_rows`, and the aggregate `check_monitoring_integrity_backlog` (all-pass case,
  each of the 4 conditions independently forced to FAIL), a ceiling-pin test, and a real-corpus
  pass test, plus a Makefile-wiring test mirroring the epic's existing check modules.
- Manual: `make agent-monitoring-validate` run against the real corpus, confirmed exit 0 (was
  exit 1 before the fix).
- Manual: `tickets/working_log.csv` re-parsed after the 9-row repair, confirmed 0 malformed rows
  remain and the diff touches exactly those 9 physical lines (verified via `git diff --stat`).
