# Test Plan — TCK-20260921-REAL-TOKEN-TELEMETRY

| Case | Verification |
|---|---|
| Basic usage extraction | `test_parse_transcript_file_extracts_basic_usage` |
| Dedup by requestId (usage repeats per content block) | `test_parse_transcript_file_dedupes_by_request_id` |
| `--since` filter excludes earlier rows | `test_parse_transcript_file_since_filter_excludes_earlier_rows` |
| Subagent path detection | `test_parse_transcript_file_detects_subagent_path` |
| Compact boundary counting | `test_parse_transcript_file_counts_compact_boundaries` |
| Tool result sizes are char counts, never content | `test_parse_transcript_file_tool_result_sizes_are_char_counts_not_content` |
| MCP tool name shortening | `test_parse_transcript_file_mcp_tool_name_shortened` |
| Missing file fails open, not an error | `test_parse_transcript_file_missing_file_returns_empty_not_error` |
| Missing root fails open (`iter_transcript_files`, `collect`) | `test_iter_transcript_files_returns_nothing_for_missing_root`, `test_collect_returns_empty_for_nonexistent_root_not_error` |
| End-to-end synthetic project tree walk | `test_collect_walks_synthetic_project_tree_end_to_end` |
| Context-size bucketing | `test_context_size_buckets_places_records_in_correct_bucket` |
| Tool attribution splits context evenly across multiple tools | `test_attribute_by_tool_splits_context_evenly_across_multiple_tools` |
| Text-only requests tracked, not dropped | `test_attribute_by_tool_tracks_text_only_requests_separately` |
| Bash family classification | `test_attribute_by_bash_family_classifies_git_subcommand` |
| Git-branch attribution (per-batch cost) | `test_attribute_by_git_branch_groups_correctly` |
| `build_report` unavailable case | `test_build_report_returns_unavailable_for_empty_records` |
| `build_report` full shape | `test_build_report_full_shape_with_synthetic_records` |
| `render_markdown` unavailable note | `test_render_markdown_unavailable_report_is_a_short_note` |
| `render_markdown` full sections present | `test_render_markdown_available_report_includes_expected_sections` |
| `generate_retro.py` section omitted when not supplied | `test_real_token_usage_section_omitted_when_not_supplied` |
| `generate_retro.py` section rendered when supplied | `test_real_token_usage_section_rendered_when_report_supplied` |
| `generate_retro.py` renders unavailable note, not empty | `test_real_token_usage_section_renders_unavailable_note_not_empty_when_no_records` |
| `retrieval_baseline_metrics.py` existing pinned test still passes | `test_baseline_report_context_tokens_marked_unavailable` (unmodified, still passing) |

All fixtures above are synthetic, built in-test via `tmp_path` and handwritten JSONL rows — no real
transcript content is read by, or copied into, any test.

## Real-world validation (read-only, nothing committed)

Executed: `python3 tools/agent-monitoring/real_token_usage.py --since 2026-09-21` against this
machine's real `~/.claude/projects/` corpus directly. Confirmed the tool runs end to end, resolves
real session role names, correctly splits main vs. subagent, and the by-git-branch attribution
surfaced this session's own then-current branch with a real, distinct request count and average
context size. Nothing from this run was written to disk or copied into any file in this repo —
observed directly in this session's own terminal output only, per the module's own "never persist
back into the repo" rule.

## Full suite run
- `pytest tests/tools/test_real_token_usage.py -v` — 21 passed.
- `pytest tests/tools/test_generate_retro.py -q -m "not slow and not extra_slow"` — 191 passed
  (167 pre-existing + 3 new, 2 pre-existing unrelated skill-staleness warnings).
- `pytest tests/tools/test_retrieval_baseline_metrics.py -q -m "not slow and not extra_slow"` —
  20 passed (existing pinned shape unaffected by the doc-correction edit).
