# Test Plan — TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS

| Case | Verification |
|---|---|
| `input_summary` never carries offset/limit for a Read call | Read `post_tool_hook.py::_input_summary()` source directly; cross-checked against real corpus rows including ones from this session's own known-ranged Read calls |
| `read_ranged` is `False` for a whole-file Read | `test_read_ranged_false_for_whole_file_read` |
| `read_ranged` is `True` when `offset` is present | `test_read_ranged_true_when_offset_present` |
| `read_ranged` is `True` when `limit` is present | `test_read_ranged_true_when_limit_present` |
| `read_ranged` is `null` for every non-Read tool | `test_read_ranged_null_for_non_read_tools` |
| Existing exact-key-set assertion on the record still holds with the new field added | `_RECORD_FIELDS` updated in `test_post_tool_hook.py`; all 22 tests in the file pass |
| `read_ranged_baseline.py` splits known/unknown correctly | `test_counts_split_correctly_across_known_and_unknown`, `test_rows_missing_ts_are_excluded_from_the_window_but_still_counted` |
| Empty corpus doesn't crash | `test_empty_corpus_reports_zero_counts_and_null_window` |
| CLI runs against the real corpus and totals reconcile | `test_cli_runs_against_real_corpus_and_prints_json` |
| Baseline script never mutates `agent-monitoring/` | `test_cli_does_not_mutate_agent_monitoring` (git-porcelain before/after) |
| New doc's frontmatter is valid | `validate_frontmatter.py docs/guidelines/retrieval_preference.md` |
| No regression in the surrounding suite | `pytest tests/tools/ tests/docs/ -m "not slow and not extra_slow" -q`: 2825 passed, 0 failed |
| Real baseline numbers, recorded for the ticket's own before/after record | `total_read_calls=41470`, `read_ranged_true_count=6` (this session's own post-change ranged reads), `read_ranged_false_count=0`, `read_ranged_unknown_count=41464`, window `2026-06-13T17:23:37Z`–`2026-09-20T04:46:56Z` |

Executed: `pytest tests/tools/test_post_tool_hook.py -v` (22 passed), `pytest
tests/tools/test_read_ranged_baseline.py -v` (5 passed), `pytest tests/tools/ tests/docs/ -m "not
slow and not extra_slow" -q` (2825 passed, 0 failed), `python3
tools/agent-monitoring/read_ranged_baseline.py` (real output recorded above), `make
knowledge-index-update` (90 files re-embedded, 0 errors).
