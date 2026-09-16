# Test Plan — TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION

| Case | Verification |
|---|---|
| Item 2 reports two distinct conditions | `check_monitoring_integrity_backlog()` returns 5 results; index 0 = historical, index 1 = live |
| Live condition names offending ticket_ids | `test_item2_live_condition_fails_on_any_planted_post_freeze_miss_and_names_the_ticket` — planted post-freeze row, asserts the ticket_id string appears in the evidence |
| Historical condition unaffected by a live-only miss | same test, asserts `results[0]["status"] == "PASS"` |
| Pre-freeze row does not trip the live condition | `test_item2_live_condition_unaffected_by_a_pre_freeze_row` |
| Historical ceiling re-derived, not carried over | Measured directly against the live corpus at implementation time: 219 historical, 0 live |
| A legitimate reopen moves working_log_duplicate's count but cannot fail CI | `test_a_legitimate_reopen_moves_the_count_but_cannot_fail_ci` — synthetic single-phase vs. two-phase closure, confirms the count differs, confirms the check always reports PASS |
| A legitimate reopen moves event_seq_integrity's counts but cannot fail CI | `test_a_legitimate_reopen_moves_both_counts_but_cannot_fail_ci` — same shape |
| `monitoring_anomaly_validator.py` needs no code change | `pytest tests/tools/test_monitoring_anomaly_validator.py` — 12 passed unmodified |
| `tool_call_count_mismatch`/`vocabulary_drift` untouched | Confirmed via `git diff` — zero changes to `tool_call_count_mismatch_check.py`; `monitoring_anomaly_validator.py`'s own `check_vocabulary_drift()` untouched |

Executed: `pytest tests/tools/test_monitoring_integrity_backlog_check.py tests/tools/test_working_log_duplicate_check.py tests/tools/test_event_seq_integrity_check.py tests/tools/test_monitoring_anomaly_validator.py -v` — 49 passed. Full `tests/tools/` suite (run together with this batch's other three tickets): 2735 passed, 0 failed.
