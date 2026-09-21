# Test Plan — TCK-20260916-HEADROOM-HARM-CHECK-BASELINE

| Case | Verification |
|---|---|
| Window filtering excludes rows before `window_start_ts` | `test_window_excludes_rows_before_window_start` |
| DONE-rate and per-event failed/blocked rate computed correctly | `test_done_rate_and_event_rates_computed_correctly` |
| `reason_code` frequency only counts present codes | `test_reason_code_frequency_only_counts_present_codes` |
| `tool_call_count` per phase excludes `None`, never fabricates a 0 | `test_tool_call_count_per_phase_excludes_none_not_treated_as_zero` |
| Hand-orchestration caveat fires when all counts are genuinely zero | `test_hand_orchestration_caveat_present_when_all_counts_are_zero` |
| Hand-orchestration caveat absent when real nonzero counts exist | `test_hand_orchestration_caveat_absent_when_real_nonzero_counts_present` |
| `session_id` population rate computed correctly | `test_session_id_population_rate` |
| Empty window doesn't crash | `test_empty_window_does_not_crash` |
| New CLI flag produces a distinct, additive report shape | `test_cli_harm_check_flag_produces_distinct_report_shape` |
| Flag-less default CLI behavior is unchanged (protects the other ticket's pinned test) | `test_cli_without_flag_still_produces_the_original_pinned_report_shape` |
| New CLI path never mutates `agent-monitoring/` | `test_cli_does_not_mutate_agent_monitoring` |
| Existing `retrieval_baseline_metrics.py` tests are unaffected | `pytest tests/tools/test_retrieval_baseline_metrics.py -v`: 20 passed |
| No regression in the surrounding suite | `pytest tests/tools/ -m "not slow and not extra_slow" -q`: 2767 passed, 0 failed |
| Real baseline recorded against the real corpus | `python3 tools/agent-monitoring/retrieval_baseline_metrics.py --harm-check-window-start 2026-09-16` — output recorded verbatim in the ticket |

Executed: `pytest tests/tools/test_headroom_harm_check_baseline.py -v` (11 passed, new file),
`pytest tests/tools/test_retrieval_baseline_metrics.py -v` (20 passed), `pytest tests/tools/ -m
"not slow and not extra_slow" -q` (2767 passed, 0 failed), the real CLI command against the
current corpus (output recorded in the ticket's Test Summary/Completion Summary).
