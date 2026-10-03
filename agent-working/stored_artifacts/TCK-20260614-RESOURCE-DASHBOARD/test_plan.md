---
ticket_id: TCK-20260614-RESOURCE-DASHBOARD
date: 2026-06-14
---

# Test Plan: TCK-20260614-RESOURCE-DASHBOARD

File: `tests/unit/cli/test_diagnostics_resources.py`

| # | Test Class | Test | Coverage |
|---|-----------|------|----------|
| 1 | TestFormatTable | test_table_contains_subsystem_names | Names in output |
| 2 | TestFormatTable | test_table_contains_state | State column present |
| 3 | TestFormatTable | test_table_shows_usage_fraction_when_budget_set | % usage shown |
| 4 | TestFormatTable | test_table_empty_reports_shows_notice | Empty → notice |
| 5 | TestFormatTable | test_table_has_header | Header row present |
| 6 | TestFormatJson | test_json_is_valid | Valid JSON list |
| 7 | TestFormatJson | test_json_contains_required_keys | All keys present |
| 8 | TestFormatJson | test_json_empty_is_empty_array | Empty → [] |
| 9 | TestHasDegraded | test_no_degraded_returns_false | OK+WARN → False |
| 10 | TestHasDegraded | test_one_degraded_returns_true | DEGRADED → True |
| 11 | TestHasDegraded | test_empty_returns_false | Empty → False |
| 12 | TestRunDiagnosticsResources | test_exit_code_0_when_all_ok | Exit 0 on OK |
| 13 | TestRunDiagnosticsResources | test_exit_code_1_on_degraded | Exit 1 on DEGRADED |
| 14 | TestRunDiagnosticsResources | test_table_output_written | Table written to out |
| 15 | TestRunDiagnosticsResources | test_json_output_valid | JSON written to out |
| 16 | TestRunDiagnosticsResources | test_offline_mode_no_kernel | No crash without kernel |
| 17 | TestKernelResourceSnapshot | test_resource_snapshot_returns_list | Returns list shape |
| 18 | TestKernelResourceSnapshot | test_resource_snapshot_includes_observability | obs in list |

Run: `pytest tests/unit/cli/test_diagnostics_resources.py -v`
