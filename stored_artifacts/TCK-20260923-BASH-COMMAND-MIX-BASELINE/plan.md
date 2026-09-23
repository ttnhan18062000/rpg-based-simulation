# Plan — TCK-20260923-BASH-COMMAND-MIX-BASELINE

## Steps
1. New module `tools/agent-monitoring/bash_command_mix.py`:
   - `week_shards()` / `load_tools_rows_with_line_count()` / `load_tools_rows()` — glob
     `agent-monitoring/data/*/tools.jsonl`, optionally bounded to an inclusive `[since_week,
     through_week]` ISO-week range (string comparison, matches `generate_retro.py`'s own
     `iso_week`/`week_range` convention). Reuses `validate.py::load_jsonl_with_line_count` per
     shard — one read per shard, race-free against concurrent hook appends.
   - `bash_head(input_summary)` — first whitespace-split token, `"?"` for empty/missing.
   - `bash_subcommand_key(head, input_summary)` — `head` alone for most commands; `head +
     truncated second word` for `git`/`gh`/`make`/`python3`/`grep`/`rg` (the heads this batch's
     own measurement broke down further).
   - `build_bash_mix_report(rows, since_week, through_week)` — total rows, total Bash calls,
     `bash_head_counts`/`bash_head_shares`, `bash_subcommand_counts`, `cd_calls`/
     `cd_share_of_bash_calls` (kept as one explicit number, not fragmented like
     `real_token_usage.py`'s per-destination cd family), `grep_calls`, `search_docs_calls`
     (exact `mcp__knowledge-search__search_docs` tool-name match), `grep_to_search_docs_ratio`
     (a labeled string, never a fabricated value, when `search_docs_calls == 0`).
   - `render_markdown(report)` — human-readable table output (default CLI mode).
   - `main()` — argparse CLI: `--data-dir` (testing override), `--since-week`, `--through-week`,
     `--json` (machine-readable report for before/after diffing).
2. Tests: `tests/tools/test_bash_command_mix.py` — unit tests for the pure classifiers and
   `build_bash_mix_report` (synthetic fixtures, no I/O), a `tmp_path`-constructed week-range glob
   test, an ast-based reuse guard (must import `load_jsonl_with_line_count`, must never call
   `read_text`/`read_bytes`/`readlines` directly), and real-corpus integration tests (sanity-check
   reconciliation, read-only guard via file-size snapshot, CLI smoke tests in both markdown and
   `--json` modes).
3. Docs: add a "Bash Command Mix Baseline" section to `docs/agent-monitoring/README.md`, matching
   the sibling "Agent Tool-Usage Baseline"/"Real Token Usage" sections' length and tone.
4. Ticket + staging artifacts per CLAUDE.md ticket format; hand-orchestrated closure recording
   (`record_hand_orchestrated_closure.py`) since this batch is not going through the `Workflow`
   tool's `implement-ticket.js` pipeline.

## Explicitly not doing
- **Not** re-promoting `token_retro.py`/`token_report.py`/`token_by_tool.py` — their logic
  already shipped as `tools/agent-monitoring/real_token_usage.py` (TCK-20260921). Re-porting them
  would duplicate tested, already-shipped code. See `investigation.md` for the full comparison.
- **Not** wiring a new section into `generate_retro.py` — this ticket's own scope is the
  standalone, tested module Batch B's tickets 2/3 need as a before/after baseline; a retro-report
  section is a separate, optional follow-up, not required for that purpose (mirrors
  `real_token_usage.py`'s own precedent of shipping the module and CLI as the primary deliverable,
  with retro wiring as a related-but-separable addition).
- **Not** distinguishing `Grep`-tool-name calls from `Bash`-classified grep calls — this
  environment never records a distinct `Grep` tool name (confirmed in
  `generate_retro.py::build_raw_investigation_count_section`'s own comment); all grep-flavored
  investigation happens through `Bash`, which is exactly what this module classifies.

## Acceptance-criteria map
- "Promote the measurement into `tools/agent-monitoring/`" → `bash_command_mix.py` (new).
- "Re-runnable over an arbitrary week range, before/after in one command" →
  `--since-week`/`--through-week` + `--json` flags.
- "`bash_mix.py` reproduces the table... simplest starting point" → `render_markdown()`'s "Bash
  command head mix" table reproduces the same shape, verified against real data.
- Tested, read-only, no fabricated ratios → `tests/tools/test_bash_command_mix.py` (20 tests),
  `grep_to_search_docs_ratio`'s explicit zero-denominator guard.
