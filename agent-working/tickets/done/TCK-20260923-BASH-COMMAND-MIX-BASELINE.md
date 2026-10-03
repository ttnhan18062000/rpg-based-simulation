---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260923-BASH-COMMAND-MIX-BASELINE
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, observability, process-improvement]
---

# TCK-20260923-BASH-COMMAND-MIX-BASELINE

## Title
Promote Bash command-mix and grep:search_docs ratio measurement into a tested
`tools/agent-monitoring/` module — Batch B ticket 1 of 3 (context/token cost reduction)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`agent-working-design` dispatched Batch B (theme: context/token cost reduction) as three tickets,
this one first because tickets 2 and 3 (an advisory anti-`cd`-prefix hook, and an advisory
search-before-grep nudge) are unfalsifiable without a repeatable, provable before/after baseline.
Peer-measured finding over `agent-monitoring/data/2026-W3*/tools.jsonl` (W30-W39): 114,254 Bash
calls, `cd` the single largest head at 22% (24,875 calls, not previously broken out in the
2026-09-21 token retro) — the driver for ticket 2. Also cited: 23,237 grep-flavored Bash calls
against 184 `search_docs` calls — the driver for ticket 3. Source scratch scripts
(`bash_mix.py`/`token_retro.py`/`token_report.py`/`token_by_tool.py`) live in a peer session's
scratchpad, not the repo.

## Scope
- New `tools/agent-monitoring/bash_command_mix.py`: read-only, sourced from
  `agent-monitoring/data/*/tools.jsonl`, re-runnable over an arbitrary inclusive ISO-week range
  (`--since-week`/`--through-week`) so a before/after comparison is one command per side.
  Produces: total Bash calls and share of all rows; Bash command-head call-count mix
  (`bash_head_counts`/`bash_head_shares`); a subcommand breakdown for `git`/`gh`/`make`/`python3`/
  `grep`/`rg`; `cd_calls`/`cd_share_of_bash_calls` as one explicit, unfragmented number; and a
  `grep_calls` vs. exact `mcp__knowledge-search__search_docs`-call-count `grep_to_search_docs_
  ratio` (a labeled string, never fabricated, when the denominator is zero).
- `docs/agent-monitoring/README.md`: new "Bash Command Mix Baseline" section.
- `tests/tools/test_bash_command_mix.py`: full coverage per `test_plan.md`.

## Out of Scope
- Re-promoting `token_retro.py`/`token_report.py`/`token_by_tool.py` — their logic already shipped
  as `tools/agent-monitoring/real_token_usage.py` (`TCK-20260921-REAL-TOKEN-TELEMETRY`); see
  `investigation.md` for the full comparison against this ticket's own module.
- Wiring a new section into `generate_retro.py` — this ticket delivers the standalone module and
  CLI Batch B's tickets 2/3 need; retro wiring is a separable future addition, not required here.
- Tickets 2 and 3 of this same batch (the advisory hooks themselves) — separately scoped, and
  depend on this ticket's module for their own before/after evidence.

## Acceptance Criteria
- [x] `tools/agent-monitoring/bash_command_mix.py` exists, read-only, reuses
      `validate.py::load_jsonl_with_line_count` (no direct file read reimplementation), and never
      fabricates the grep:search_docs ratio when `search_docs_calls == 0`.
- [x] Re-runnable over an arbitrary inclusive ISO-week range via `--since-week`/`--through-week`;
      `--json` flag for machine-readable before/after diffing.
- [x] Reproduces the batch's own cited head-mix table shape (`cd`/`grep`/`git`/`python3` head
      counts, `grep -n`/`git status`/`git diff`/`git add`/`python3 -c` subcommand breakdown),
      verified against the real corpus for the same W30-W39 window.
- [x] `docs/agent-monitoring/README.md` gains a "Bash Command Mix Baseline" section.
- [x] All 20 new tests pass; sibling regression suite (`test_agent_tool_usage_baseline.py`,
      `test_real_token_usage.py`, `test_validate_agent_monitoring.py`) passes unmodified.

## Related Tickets
- `TCK-20260921-REAL-TOKEN-TELEMETRY` (done) — ships the token-side (context-token attribution,
  by day/model/session/branch) half of the peer's scratch-script logic; this ticket ships the
  raw-call-count Bash-mix half that module doesn't cover, from a different (git-committed) source.
- `TCK-20260904-AGENT-TOOL-USAGE-BASELINE` (done) — per-agent tool-usage table from the same
  `tools.jsonl` source; this ticket adds command-head classification that one doesn't have.
- Batch B tickets 2 and 3 (not yet filed) — the advisory `cd`-prefix hook and search-before-grep
  nudge this ticket's module provides the baseline for.

## Related Docs
- `docs/agent-monitoring/README.md` — new "Bash Command Mix Baseline" section.
- `docs/agent-monitoring/schema.md` — `tools.jsonl`'s `input_summary` field (source data shape).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260923-BASH-COMMAND-MIX-BASELINE/` — `investigation.md`, `plan.md`,
  `test_plan.md`.

## Related Code Areas
- `tools/agent-monitoring/bash_command_mix.py` (new)
- `tests/tools/test_bash_command_mix.py` (new)
- `docs/agent-monitoring/README.md`
- `tools/agent-monitoring/validate.py` (`load_jsonl_with_line_count`, reused not modified)

## Assumptions / Open Questions
- The peer's cited `search_docs` count (184) does not match this ticket's own real-corpus
  measurement (1,535, independently verified via direct per-shard `grep -c`) for the same
  `2026-W30`..`2026-W39` window — the peer's figure appears stale relative to the current,
  continuously-growing corpus. The qualitative conclusion (grep badly outweighs `search_docs`,
  ratio ~15.5:1 even corrected) is unchanged. Flagged back to `agent-working-design` with evidence
  rather than silently reproduced; this ticket's own module is now the authoritative source.
- `bash_head_counts`/`bash_subcommand_counts` classify by `input_summary`'s first (and, for a
  fixed head set, second) whitespace-split token only — a simple heuristic, matching the peer's
  own already-reviewed prototype's precision level, not a general shell-command parser.

## Implementation Notes
Investigation (see `investigation.md`) found the request as originally framed ("promote the four
scratch scripts") would have duplicated already-shipped code: `real_token_usage.py`
(`TCK-20260921-REAL-TOKEN-TELEMETRY`) already promotes `token_retro.py`/`token_report.py`/
`token_by_tool.py` in full, including a Bash-family attribution — by context tokens, from
developer-machine-only transcripts, with `cd` fragmented by destination directory. The genuinely
new piece was `bash_mix.py`'s raw call-count Bash-head mix, sourced from the git-committed
`tools.jsonl` corpus rather than transcripts, kept as one unfragmented `cd` total, plus a new
grep-vs-`search_docs` ratio metric `generate_retro.py` explicitly documents as unavailable via its
own existing `read_to_search_ratio` (Read-count proxy, not real grep-call counting). Also found and
fixed a data-shape bug carried over from the scratch prototype: `bash_mix.py`'s regex assumed
`input_summary` was a Python dict-repr string; the real schema is the plain truncated command
string, parsed directly via `.split()`.

Ran the new module against the peer's own cited `2026-W30`..`2026-W39` window and cross-checked
every number: Bash calls, `cd`, `grep`, `git`, `python3` head counts, and subcommand breakdown all
matched (within ~2%, consistent with two more days of corpus growth) — except `search_docs`, which
this ticket's module puts at 1,535, independently confirmed via a direct per-shard `grep -c`
sum-check, not just the module's own output. That discrepancy is disclosed above rather than
silently reproducing the peer's stale number.

## Test Summary
- `pytest tests/tools/test_bash_command_mix.py -v` — 20 passed.
- `pytest tests/tools/test_agent_tool_usage_baseline.py tests/tools/test_real_token_usage.py tests/tools/test_validate_agent_monitoring.py -q -m "not slow and not extra_slow"` — 67 passed
  (pre-existing, unmodified).

## Files Changed
- `tools/agent-monitoring/bash_command_mix.py` (new)
- `tests/tools/test_bash_command_mix.py` (new, 20 tests)
- `docs/agent-monitoring/README.md` — new "Bash Command Mix Baseline" section.
- `staging_artifacts/TCK-20260923-BASH-COMMAND-MIX-BASELINE/` (new).

## Completion Summary
Built `tools/agent-monitoring/bash_command_mix.py`, a read-only, tested module over
`agent-monitoring/data/*/tools.jsonl` giving Batch B's remaining two tickets a repeatable,
re-runnable-over-an-arbitrary-week-range before/after baseline: Bash command-head/subcommand
call-count mix (with `cd` kept as one explicit number), and a grep-flavored-Bash-call vs.
`search_docs`-call ratio that closes a gap `generate_retro.py` already documents as unavailable
via its own existing proxy metric. Investigation found and avoided duplicating already-shipped
code (`real_token_usage.py` from a prior ticket already covers the token/context-attribution half
of the peer's scratch-script logic) and caught two real issues before they shipped: a data-shape
bug in the scratch prototype's regex, and a stale `search_docs` call count in the peer's own cited
numbers (independently corrected and verified against the real corpus). 20 new tests, all passing;
sibling regression suite unaffected. No known material gap left unstated.
