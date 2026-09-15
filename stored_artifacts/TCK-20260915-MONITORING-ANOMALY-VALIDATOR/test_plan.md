# Test Plan — TCK-20260915-MONITORING-ANOMALY-VALIDATOR

- `tests/tools/test_validate_agent_monitoring.py`: existing drift-report tests re-run unchanged to
  prove `compute_vocabulary_drift_counts()`'s extraction is byte-identical to the prior inline
  logic (15 tests, including the `TestRegressionParity`/`TestDriftReportsUnaffectedByWeekShardMigration`
  classes).
- `tests/tools/test_record_events.py`, other vocabulary-consuming tests: re-run to confirm the 6
  new `vocabulary.py` registrations don't change any existing warn-only behavior for already-known
  literals.
- `tests/tools/test_monitoring_anomaly_validator.py` (new, 12 tests):
  - `check_vocabulary_drift`: clean-pass case, registered-literal-not-flagged case (proves
    `orchestrator` specifically no longer drifts), agent/tier FAIL cases via monkeypatched
    ceilings, a ceiling-pin test.
  - `check_ts_shape_and_unknown_week`: clean-pass case, a deliberately-planted bad record
    (`start_ts: None`) proving detection (AC #4), not just clean reporting.
  - `check_monitoring_anomalies`: tags every result with its source check; all-pass on a clean
    synthetic corpus; a real-corpus pass test.
  - Wiring: Makefile target presence, and a subprocess-level test asserting the CLI's real stdout
    contains `MARKER:`/`"check":`/`"status":` content (AC #3 — presence of output, not merely a
    return code).
- Manual: `make monitoring-anomaly-validate` against the real corpus — all 9 conditions PASS,
  exit 0.
- Manual: full `tests/tools/` suite re-run for final regression confirmation.
