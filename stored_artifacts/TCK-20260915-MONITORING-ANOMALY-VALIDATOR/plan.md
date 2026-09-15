# Plan — TCK-20260915-MONITORING-ANOMALY-VALIDATOR

1. Investigate all 6 candidate checks against sibling-ticket reality before writing any new code
   (done — see investigation.md).
2. Fix the real defect found: register 6 legitimate agent literals in
   `tools/agent-monitoring/vocabulary.py` (`orchestrator` under both `implement-ticket` and
   `create-tickets`, `context-packet-wrapper` and `implement-ticket` under `implement-ticket`,
   `concern-investigator` and `write-sequence` under `create-tickets`, `implement-epic` under
   `implement-epic`), each with a confirming comment matching the file's existing standard.
3. Extract `compute_vocabulary_drift_counts()` from `validate.py`'s existing
   `compute_drift_report()` (structured data, not just formatted text) so a ratchet check can
   consume raw counts — byte-identical output proven via the existing drift-report tests.
4. Build `tools/gate_checks/monitoring_anomaly_validator.py`: a new `check_vocabulary_drift()` for
   the genuine residual (agent 162 / tier 2), plus a thin `check_ts_shape_and_unknown_week()`
   wrapper reusing ticket 7's own items 4/5 functions (not item 2 — presence is `validate.py`'s
   domain), aggregating with tickets 1/3/4's existing check functions into one
   `check_monitoring_anomalies()` surface.
5. Wire a `monitoring-anomaly-validate` Makefile target; pin it with a test asserting real stdout
   content (not just a return code) per AC #3, and a deliberately-planted-bad-record test proving
   detection (not just clean reporting) per AC #4.
6. Run full affected regression scope; confirm the real corpus passes every ratchet.
