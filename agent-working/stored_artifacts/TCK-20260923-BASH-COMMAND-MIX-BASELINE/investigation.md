# Investigation — TCK-20260923-BASH-COMMAND-MIX-BASELINE

## Source of the request
`agent-working-design` dispatched Batch B (context/token cost reduction), ticket 1 of 3, with a
peer-provided measurement: over `agent-monitoring/data/2026-W3*/tools.jsonl` (W30-W39), 114,254
Bash calls, with `cd` the single largest head at 22% (24,875 calls) — a new finding not broken out
in the 2026-09-21 token retro, and the driver behind ticket 2 (advisory anti-`cd`-prefix hook).
Also cited: 23,237 grep-flavored Bash calls against only 184 `search_docs` calls in the same
window — the driver behind ticket 3. Ticket 1's job is to promote this into a tested, repeatable
`tools/agent-monitoring/` module so both later tickets have a provable before/after baseline.
Source scratch scripts (peer's scratchpad, not yet in the repo):
`bash_mix.py`/`token_retro.py`/`token_report.py`/`token_by_tool.py` at
`/tmp/claude-1000/.../agent-monitoring-data-quality-fix/5e91d3b6-4116-4322-9536-73ed39455e1e/scratchpad/`.

## Context scan (search_docs / graphify, before any grep)
`search_docs` for "Bash command mix token cost cd prefix grep search_docs agent-monitoring
baseline" surfaced `TCK-20260921-REAL-TOKEN-TELEMETRY` (done) and `TCK-20260904-AGENT-TOOL-USAGE-
BASELINE` (done) as the two closest prior tickets. Reading both in full changed the scope of this
ticket materially from a naive "port all four scratch scripts":

- **`tools/agent-monitoring/real_token_usage.py`** (from TCK-20260921) already promotes
  `token_retro.py`/`token_report.py`/`token_by_tool.py`'s logic in full — by day/model/session/
  git-branch, context-size buckets, tool attribution, and `attribute_by_bash_family` (Bash command
  family attribution). It reads `~/.claude/projects/**/*.jsonl` (developer-machine-only real
  transcripts), attributing **context tokens**, not raw call counts. Its `_bash_family()` also
  special-cases `cd` by appending the destination directory's last path segment
  (`cd worktrees`, `cd repo`, ...), which *fragments* the single "cd" total this batch's own
  finding depends on keeping as one number. Porting `token_retro.py`/`token_report.py`/
  `token_by_tool.py` again would be a near-duplicate of already-shipped, already-tested code.
- **`tools/agent-monitoring/agent_tool_usage_baseline.py`** (from TCK-20260904) already promotes
  a per-agent Bash-inclusive tool-usage table from `tools.jsonl`, but never classifies the Bash
  command head itself (no `cd`/`grep`/`git` breakdown).
- **`generate_retro.py::build_raw_investigation_count_section`** already computes a
  `read_to_search_ratio` and documents, explicitly, why it can't compute a real grep:search_docs
  ratio: "no distinct `Grep` tool name is ever recorded ... grep-equivalent work runs through the
  catch-all `Bash` tool, which is excluded here." This is precisely the gap `bash_mix.py`'s
  regex-based command-head classification was built to close, and precisely the gap this ticket
  should close — not a duplicate, a real complement.

Conclusion: the only genuinely new promotion needed is **`bash_mix.py`**'s logic (raw Bash
command-head/subcommand call-count mix), sourced from `agent-monitoring/data/*/tools.jsonl` (git-
committed, available to any session or CI — unlike `real_token_usage.py`'s transcript source),
made re-runnable over an arbitrary ISO week range, plus a grep-head-count-vs-`search_docs`-count
ratio using the same command-head classifier. `token_retro.py`/`token_report.py`/`token_by_tool.py`
are NOT re-promoted — their functionality already ships as `real_token_usage.py`.

## Real schema verification (not the scratch script's assumed shape)
`bash_mix.py`'s own regex (`re.search(r"'command':\s*[\"']([^\"']{0,100})", s)`) assumed
`input_summary` was a Python dict-repr string. Checked the real schema directly against
`agent-monitoring/data/2026-W37/tools.jsonl`: `input_summary` for a `Bash` row is the plain
(120-char-truncated) command string itself, e.g. `"cd /home/.../worktrees/m2-foundation"` — no
dict wrapper. The new module parses this directly (`.split()`), not via the scratch script's
regex, which would silently fail to match on the real data shape.

## Real-corpus verification of the peer's own cited numbers
Ran the new module against `--since-week 2026-W30 --through-week 2026-W39` (the same window the
peer cited): 116,189 Bash calls (peer: 114,254 — ~2% higher, consistent with two further days of
corpus growth since their snapshot), `cd` 24,943 calls / 21.5% (peer: 24,875 / 22% — matches),
`grep` 23,806 calls (peer: 23,237 — matches), `git` 12,745 (peer: 12,404 — matches), `python3`
11,656 (peer: 11,470 — matches). **`search_docs` calls: 1,535** (peer: 184) — independently
verified by a direct `grep -c '"tool": "mcp__knowledge-search__search_docs"'` per shard, summed by
hand: 48+115+179+248+306+178+282+104+58+17 = 1,535, matching the module exactly. The peer's "184"
figure is stale relative to the current corpus (likely measured over a narrower window or an
earlier corpus snapshot) — flagged back to `agent-working-design` with this evidence rather than
silently reproduced. The qualitative conclusion (`search_docs` badly underused relative to grep)
still holds: grep:search_docs ratio is ~15.5:1 even with the corrected, larger `search_docs` count.

## Reuse decisions
- Shard loading: reuses `validate.py::load_jsonl_with_line_count` per shard (same race-free,
  single-read-per-shard pattern `agent_tool_usage_baseline.py`'s own `_with_line_count` variant
  uses), not a fresh file reader. `load_data_glob`/`load_data_glob_with_line_count` themselves
  weren't reusable as-is because they don't support a week range — this ticket needs one for the
  before/after comparison, so a thin week-filtering wrapper around the same per-shard primitive
  was written instead of extending the two existing sibling call sites' contract.
- `SEARCH_DOCS_TOOL_NAME` uses the exact `mcp__knowledge-search__search_docs` tool-name string,
  not `generate_retro.py`'s broader `SEARCH_TOOL_NAMES` set (which also includes `ToolSearch`/
  `WebSearch`) — this batch's own finding was specifically about `search_docs`, not search tooling
  broadly, so the narrower, exact metric was kept rather than silently widening it.
