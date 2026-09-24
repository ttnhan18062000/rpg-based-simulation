# Test Plan — TCK-20260923-BASH-COMMAND-MIX-BASELINE

## New tests (`tests/tools/test_bash_command_mix.py`)
1. `test_bash_head_returns_first_word` — normal flow.
2. `test_bash_head_handles_empty_or_missing_summary` — edge case (empty string, `None`,
   whitespace-only).
3. `test_bash_subcommand_key_breaks_down_known_heads_only` — normal flow, the exact
   `git`/`grep`/`python3` breakdown granularity the batch's own measurement used.
4. `test_bash_subcommand_key_leaves_non_breakdown_heads_bare` — edge case (`ls`/`cd`/`echo` stay
   bare heads, not fragmented).
5. `test_bash_subcommand_key_single_word_command_falls_back_to_head` — edge case (no second word).
6. `test_report_counts_cd_and_head_mix_correctly` — normal flow, core metric.
7. `test_report_grep_to_search_docs_ratio_computed_when_search_docs_present` — normal flow.
8. `test_report_ratio_is_labeled_string_not_fabricated_when_zero_search_docs` — failure/edge mode:
   proves the ratio is never a fabricated divide-by-zero substitute.
9. `test_report_empty_corpus_does_not_divide_by_zero` — edge case, whole-report level.
10. `test_report_rg_head_counts_toward_grep_calls_too` — normal flow (rg alias).
11. `test_report_carries_since_through_week_labels_through` — normal flow, report metadata.
12. `test_render_markdown_includes_cd_and_ratio_lines` — normal flow, rendering.
13. `test_week_shards_filters_to_inclusive_range` — normal flow, the before/after mechanism
    itself.
14. `test_load_tools_rows_respects_week_range` — normal flow.
15. `test_load_tools_rows_with_line_count_matches_row_count` — regression-prone path (race-free
    single-read guarantee).
16. `test_reuses_load_jsonl_with_line_count_not_a_fresh_reader` — architecture test: proves reuse,
    not reimplementation, of the shard reader.
17. `test_sum_of_head_counts_matches_total_bash_calls_on_real_corpus` — real-corpus sanity check
    (reconciliation).
18. `test_script_is_read_only_against_real_agent_monitoring_data` — architecture test: read-only
    guard against `agent-monitoring/data/`.
19. `test_cli_runs_against_real_corpus_and_prints_markdown` — real-corpus CLI smoke test.
20. `test_cli_runs_with_json_flag_and_prints_valid_report` — real-corpus CLI smoke test,
    machine-readable mode.

## Regression scope
- `pytest tests/tools/test_bash_command_mix.py -v` (new).
- `pytest tests/tools/test_agent_tool_usage_baseline.py tests/tools/test_real_token_usage.py tests/tools/test_validate_agent_monitoring.py -q -m "not slow and not extra_slow"` —
  confirms no regression in the sibling modules this ticket reads alongside (`validate.py`'s
  shared reader, the two closely-related prior baselines).
- Not the full suite (`pytest tests/`) — scoped to the domain under modification per CLAUDE.md's
  Testing Rule.

## Coverage check
Normal flow: classification, aggregation, rendering, week-range filtering, CLI (both output
modes). Edge cases: empty summary, single-word command, empty corpus, zero `search_docs` calls.
Failure modes: the zero-denominator ratio guard (labeled string, not a crash or fabricated 0/∞).
Regression-prone paths: the race-free single-read-per-shard reconciliation (mirrors a real,
previously-fixed race in the sibling `agent_tool_usage_baseline.py` module).
