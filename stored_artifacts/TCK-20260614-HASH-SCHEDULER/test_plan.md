---
ticket_id: TCK-20260614-HASH-SCHEDULER
date: 2026-06-14
---

# Test Plan: TCK-20260614-HASH-SCHEDULER

File: `tests/unit/engine/test_hash_scheduler.py`

| # | Test | Coverage |
|---|------|----------|
| 1 | `test_hash_mode_values` | HashMode.FULL=="full", LIGHT=="light" |
| 2 | `test_is_runtime_error` | HashScheduleViolation is RuntimeError |
| 3 | `test_full_hash_allowed_at_tick_zero` | tick=0 passes schedule check |
| 4 | `test_full_hash_allowed_at_run_end_tick` | tick==run_end_tick passes |
| 5 | `test_full_hash_allowed_with_certification_reason` | reason="certification" passes |
| 6 | `test_full_hash_allowed_with_audit_reason` | reason="audit" passes |
| 7 | `test_full_hash_allowed_with_replay_reason` | reason="replay" passes |
| 8 | `test_full_hash_raises_outside_sanctioned_boundary` | mid-tick, no reason → raises |
| 9 | `test_full_hash_raises_with_unknown_reason` | unknown reason → raises |
| 10 | `test_light_hash_always_allowed` | LIGHT never raises, returns 32-char hex |
| 11 | `test_light_hash_default_mode` | default mode is LIGHT |
| 12 | `test_light_hash_is_fast` | 100 calls < 10ms total |
| 13 | `test_light_hash_changes_on_tick` | different tick → different hash |
| 14 | `test_light_hash_no_json_serialization` | json.dumps not called |
| 15 | `test_allows_tick_zero` | allow_full_hash_at(0, "") |
| 16 | `test_allows_run_end_tick` | allow_full_hash_at(50, "") with run_end=50 |
| 17 | `test_rejects_mid_run_tick_no_reason` | allow_full_hash_at(42, "") → False |
| 18 | `test_run_end_tick_negative_one_means_unset` | run_end=-1 → mid-tick rejected |
| 19 | `test_no_casual_get_hash_call_when_replay_disabled` | architecture guard |

Run: `pytest tests/unit/engine/test_hash_scheduler.py -v`
