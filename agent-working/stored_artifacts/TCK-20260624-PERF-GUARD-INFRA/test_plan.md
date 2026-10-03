---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260624-PERF-GUARD-INFRA
date: 2026-06-24
---

# Test Plan: TCK-20260624-PERF-GUARD-INFRA

## Unit tests (`tests/unit/perf/test_perf_guard.py`)

| # | Test | Assertion |
|---|---|---|
| 1 | `test_baseline_schema_valid` | `perf_baselines.json` loads, `version==1`, entries is dict |
| 2 | `test_perf_budget_fixture_fail_on_missing_entry` | Missing entry → `pytest.fail` raised |
| 3 | `test_perf_budget_assert_within_budget_pass` | 10ms budget ±20%: 11ms passes |
| 4 | `test_perf_budget_assert_within_budget_fail` | 10ms budget ±20%: 13ms fails (`AssertionError`) |
| 5 | `test_perf_budget_assert_memory_skip_when_null` | `memory_kb: null` → no memory assertion even with measured_kb |
| 6 | `test_snapshot_rss_returns_positive` | `/proc/self/statm` → result > 0 |

## Integration check
- `python3 -m pytest tests/perf/ -m "not slow" --collect-only -q` — collection must succeed
- `python3 -m pytest tests/unit/perf/test_perf_guard.py -v` — all 6 pass

## Regression guard
- Existing fixtures `perf_harness`, `perf_reporter`, `perf_report_dir` must still be importable
