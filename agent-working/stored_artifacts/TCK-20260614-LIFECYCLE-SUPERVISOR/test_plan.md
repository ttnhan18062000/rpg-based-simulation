---
ticket_id: TCK-20260614-LIFECYCLE-SUPERVISOR
date: 2026-06-14
---

# Test Plan: TCK-20260614-LIFECYCLE-SUPERVISOR

File: `tests/unit/engine/test_lifecycle_supervisor.py`

| # | Test Class | Test | Coverage |
|---|-----------|------|----------|
| 1 | TestShutdownReportShape | test_shutdown_report_dataclass_exists | All 7 fields present |
| 2 | TestShutdownReportShape | test_shutdown_report_defaults | Correct defaults |
| 3 | TestShutdownReportShape | test_shutdown_report_mutable | warnings list mutable |
| 4 | TestCleanShutdown | test_shutdown_returns_shutdown_result | Return type preserved |
| 5 | TestCleanShutdown | test_shutdown_report_accessible_after_shutdown | shutdown_report() type |
| 6 | TestCleanShutdown | test_shutdown_report_none_before_shutdown | Pre-shutdown is None |
| 7 | TestCleanShutdown | test_clean_shutdown_outcome_success | outcome=="SUCCESS" |
| 8 | TestCleanShutdown | test_clean_shutdown_warnings_empty | No spurious warnings |
| 9 | TestCleanShutdown | test_workers_started_is_positive | _workers_started set |
| 10 | TestCleanShutdown | test_workers_stopped_equals_started_on_clean_shutdown | accounting balanced |
| 11 | TestPendingReplayFlushesWarning | test_pending_replay_flushes_zero_no_warning | 0 flushes → quiet |
| 12 | TestPendingReplayFlushesWarning | test_pending_replay_flushes_nonzero_generates_warning | >0 → warning |
| 13 | TestBehaviorWorkerShutdown | test_behavior_worker_thread_joined_on_shutdown | Thread joined |
| 14 | TestSurvivalCountsInReport | test_survival_counts_captured_in_report | Counts in report |

Run: `pytest tests/unit/engine/test_lifecycle_supervisor.py -v`
