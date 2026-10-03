# Plan — TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION

## Original scope: split item 2

1. Add `FREEZE_DATE` (this ticket's own landing date, 2026-09-16) to
   `monitoring_integrity_backlog_check.py`.
2. Change `find_working_log_rows_missing_run_record()` to return `(historical, live)` instead of
   a flat list, splitting on `FREEZE_DATE`.
3. Replace `NO_RUN_RECORD_CEILING` with `NO_RUN_RECORD_HISTORICAL_CEILING` (ratchet, re-derived at
   implementation time) and `NO_RUN_RECORD_LIVE_CEILING` (zero-tolerance, always 0).
4. `check_monitoring_integrity_backlog()` now returns 5 conditions instead of 4; the live
   condition's evidence names the specific offending `ticket_id`s.
5. Re-derive the historical ceiling and confirm live reads 0 (the three epic closures already
   remediated).

## Widened scope: apply the same test to the sibling ratchets

6. For `working_log_duplicate_check.py` and `event_seq_integrity_check.py`: confirmed via their
   own pre-existing docstrings that both are dominated by the same legitimate multi-invocation
   mechanism a historical/live split doesn't fit as cleanly as outright removal — prefer removing
   the gate and keeping the reported number, per the attribution-floor precedent, rather than a
   second two-condition split.
7. Remove `DUPLICATE_TICKET_ID_CEILING` and the blocking path from `working_log_duplicate_check.py`;
   add `compute_working_log_duplicate_ticket_ids()` as the measurement; `check_*()` always reports
   PASS.
8. Remove `DUPLICATE_SEQ_CEILING`/`GAP_CEILING` and both blocking paths from
   `event_seq_integrity_check.py`; `check_event_seq_integrity()` always reports PASS for both
   conditions, keeping the same two-result shape `monitoring_anomaly_validator.py` already
   consumes (confirmed via grep: only that one caller, and it just reads the returned
   status/evidence — no structural change needed there).
9. Explicitly leave `tool_call_count_mismatch_check.py` and `vocabulary_drift` untouched — confirmed
   via their own history that neither moved on legitimate activity.
10. Reword the two affected `Makefile` targets' help text to reflect the report-only behavior.
