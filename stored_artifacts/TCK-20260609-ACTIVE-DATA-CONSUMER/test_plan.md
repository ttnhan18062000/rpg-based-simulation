---
ticket: TCK-20260609-ACTIVE-DATA-CONSUMER
phase: test_plan
---

# Test Plan

5 tests, all pass.

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_active_records_have_consumer_paths` | Gate: no NEW active records without consumers |
| 2 | `test_known_gaps_are_genuinely_inactive` | Known gaps still have no consumer (stale-entry guard) |
| 3 | `test_inactive_state_records_not_confused_with_active` | No state marker conflicts |
| 4 | `test_state_marked_records_are_parsed` | Scanner finds >10 active records |
| 5 | `test_implicit_consumer_families_are_scanned` | Perspective exemption is non-vacuous |
