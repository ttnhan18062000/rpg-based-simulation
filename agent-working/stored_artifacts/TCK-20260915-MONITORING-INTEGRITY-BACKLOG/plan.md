# Plan — TCK-20260915-MONITORING-INTEGRITY-BACKLOG

1. **Item 1**: add `EVENTS_REQUIRED_START = "2026-07-08"` and `_run_effective_start_ts()` to
   `tools/agent-monitoring/validate.py`; exclude "no events" errors for runs starting before that
   date (conservative: a run with no determinable start timestamp is NOT excluded). Correct the
   module docstring's exit-code claim. Verify `make agent-monitoring-validate` exits 0.
2. **Item 3 (writer)**: verify `append_working_log_row` already quotes correctly (it does — no
   code change needed); add an explicit regression test with a real comma-bearing title.
3. **Item 3 (9 rows)**: hand-map each malformed row's correct field boundaries; repair via a
   surgical one-off script that rewrites only those 9 physical lines (not a full-file
   re-serialization, which changes unrelated rows' quoting style).
4. **Items 2, 4, 5**: build one new ratchet-check module,
   `tools/gate_checks/monitoring_integrity_backlog_check.py`, with four independently-ratcheted
   conditions (item 2's missing-run-record count at the corrected 218; item 4's unusable-ts run
   and event counts at 66/55; item 5's unknown-week row count at 34). Wire a Makefile target and
   tests mirroring this epic's existing 4 check modules exactly.
5. Update `docs/agent-monitoring/schema.md` if any field-level guarantee changes (checked: none of
   these fixes change a documented field's meaning, only add exclusions/ratchets to a validator, so
   no schema.md edit is required here).
6. Run the full affected test scope; confirm `make agent-monitoring-validate` and the new
   `make monitoring-integrity-backlog-check` both pass against the real corpus.
