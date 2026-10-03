# Test Plan — TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT

- `tests/tools/test_ticket_field_values.py` (4 new tests): CLI pass/fail via subprocess, presence
  of output asserted (not just return code), `--help`, function-level import pin.
- `tests/tools/test_parity_ledger_scan.py` (5 new tests): CLI no-intersection/intersection paths
  via subprocess (synthetic ledger fixture), `--help`, a real-corpus end-to-end CLI run
  (`FAC-013`/`src/observability/event_extractor.py`, mirroring the file's own existing real-corpus
  test), function-level import pin.
- `tests/tools/test_registry_query.py` (6 new tests): CLI `--text` and `--layers` modes via
  subprocess against the real registry, no-mode-selected exits non-zero with visible stderr,
  `--help`, missing-registry-file exits non-zero, function-level import pin for both functions.
- Manual: reproduced the exact pre-fix silent-no-op behavior for all 3 modules before making any
  change (Implementation Notes' own instruction).
- Full `tests/tools/` suite re-run for final regression confirmation.
