# Investigation — TCK-20260921-REAL-TOKEN-TELEMETRY

## What already existed
The peer (agent-working-design) had prototyped the exact logic against real transcripts in
scratch scripts (`token_retro.py`, `token_report.py`, `token_by_tool.py`), measured over 14 days of
real usage for this repo: 40,039 API requests, 19.07B cache-read tokens (~78% of cost), 207M cache
writes, 21.5M output; average context 481k/request, 72% of input from requests at ≥500k, peaks
~967k, only 69 compactions; Bash 63% of context-attributed tokens; long-lived implementer sessions
(rpg-implementer (2), agent-working-implementer) dominate.

## Real data shape, confirmed by reading real transcripts directly
Assistant rows: `type: "assistant"`, `message.usage` (`input_tokens`, `cache_creation_input_tokens`,
`cache_read_input_tokens`, `output_tokens`), `message.model`, `requestId`, `gitBranch`, `timestamp`,
`message.content[]` (`tool_use` blocks carry `id`/`name`/`input`). Usage repeats on every content
block of the same message — dedupe by `requestId` (or `message.id` when absent).

`user` rows carry `tool_result` blocks (`tool_use_id`, `content` — string or list-of-blocks with
`text`), giving what came BACK from a tool call. Session role names come from `custom-title`/
`agent-name` rows, keyed by session file, not by `cwd` (several sessions share the main checkout —
same hazard shape as the confirmed `.claude/current_run` sidecar contamination).

`system` rows with `subtype: "compact_boundary"` mark a context compaction.

## Design decisions
- **Streaming, one file at a time.** Real corpus is ~1.2GB across all sessions on this machine.
  `parse_transcript_file` opens, reads line-by-line, and closes before `collect()` moves to the
  next file — never loads the whole corpus into memory at once.
- **`--since` filter is two-layered**: a coarse file-mtime pre-filter (skip files clearly untouched
  since before the cutoff — an efficiency filter only) plus the authoritative per-row `timestamp`
  check inside `parse_transcript_file`. Mirrors the peer's own scratch-script design, kept because
  it is correct: file mtime is a real signal for "was this transcript touched since X" (unlike a
  *repo* file's mtime, which reflects checkout time, not content change — a distinction already
  established elsewhere in this repo's own worktree-verification lessons).
- **Aggregates only, never raw content, is enforced structurally, not just by convention.** The
  module extracts numeric usage fields, tool NAMES, and Bash COMMAND STRINGS (needed to classify
  `git status` vs `git log`) — never a tool result's own text, never assistant/user prose. Tool
  result "content" is reduced to a character count the moment it's read; the string itself is
  never retained past that one line of code.
- **`build_report()` is separated from `collect()`** specifically so tests exercise the
  aggregation logic against synthetic `RequestRecord` objects, never touching the filesystem —
  this is what makes "nothing real may be committed" achievable while still testing real logic.
- **Fail-open by design, not by exception-handling.** A missing `~/.claude/projects/` root, or a
  root with zero matching files, is not an error anywhere in this module — `collect()` returns
  empty lists, `build_report()` returns `{"available": False, "reason": ...}`, and
  `render_markdown()`/`generate_retro.py`'s new section both render a one-line note rather than
  crash or render an empty table. Verified directly (not assumed) against a `tmp_path` that does
  not exist.
- **`generate_retro.py` wiring is opt-in (`--include-real-tokens`), not automatic.** Streaming the
  real corpus every retro run would slow down the default report for a section most retro-readers
  won't always want; `generate()` itself takes an already-built `real_token_report` dict (or
  `None`) and never touches the filesystem, so every existing test calling `generate()` directly
  is unaffected — confirmed via the full existing `test_generate_retro.py` suite still passing
  unmodified (167/167 passed before this ticket's own additions, 191/191 after).

## The two doc corrections, verified precisely before writing
- `docs/agent-monitoring/schema.md`'s "no workaround within the current platform" was false the
  moment this module existed to prove it — corrected to name the real, but differently-shaped,
  workaround (retrospective, developer-machine-only, not per-event).
- `tools/agent-monitoring/retrieval_baseline_metrics.py::build_context_tokens_section()`'s
  "platform-blocked" reason was the same false claim, reused. Its `status: "unavailable"` field
  itself stays correct and unchanged (verified against the existing pinned test,
  `test_baseline_report_context_tokens_marked_unavailable`, which only asserts `status` and
  `citation`) — this report is genuinely scoped to `agent-monitoring/data/*.jsonl` alone
  (reproducible from repo data, in CI, on any machine), and real token usage is a separate,
  machine-local data source that does not fit that report's own reproducibility contract. Added a
  `workaround` key pointing at the real tool instead of rewriting the reason to overclaim.

## Real-world validation performed, not just synthetic tests
Ran `tools/agent-monitoring/real_token_usage.py --since 2026-09-21` against this machine's real
transcripts directly (read-only CLI, nothing written anywhere, nothing copied into the repo) —
confirmed the tool runs end to end against real data shapes, correctly resolves session role names,
splits main vs. subagent, and — notably — the "by git branch" attribution genuinely surfaces
per-batch cost exactly as intended (this session's own then-current branch,
`venv-doc-fix-and-followups`, showed up with its own real request count and average context size,
distinct from every other concurrent branch/session on the machine).
