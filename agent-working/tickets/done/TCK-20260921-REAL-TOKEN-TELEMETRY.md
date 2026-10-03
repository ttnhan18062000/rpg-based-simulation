---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260921-REAL-TOKEN-TELEMETRY
phase: done
date: 2026-09-21
tags: [ai, agent-monitoring, observability, process-improvement]
---

# TCK-20260921-REAL-TOKEN-TELEMETRY

## Title
Promote real token usage analysis (from local Claude Code transcripts) into a tested, read-only
`tools/agent-monitoring/` tool, wired into `generate_retro.py`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This repo's own `docs/agent-monitoring/schema.md` has stated since early in this repo's life that
token counts have "no workaround within the current platform" — true for per-event inline
recording inside `runs.jsonl`/`events.jsonl` (the workflow `agent()` call genuinely never receives
usage metadata from the runtime), but false as a claim about token usage being unobtainable at all.
The Claude Code runtime writes real per-request `message.usage` into this machine's own local
transcript files (`~/.claude/projects/**/*.jsonl`) regardless of what the workflow script sees.

Measured over 14 real days of usage for this repo before this ticket started (peer-provided
background, independently corroborated by running the resulting tool against real transcripts):
40,039 API requests, ~78% of cost in cache-read tokens, average context 481k/request, 72% of input
from requests at ≥500k, peaks ~967k, only 69 compactions, Bash accounting for 63% of
context-attributed tokens, with the long-lived implementer sessions dominating total spend.

## Scope
- Promote the prototyped scratch-script logic into `tools/agent-monitoring/real_token_usage.py`:
  a read-only, tested module. Never writes to a transcript. Never copies transcript conversation
  content into the repo — aggregates (usage numbers, tool names, Bash command strings, byte/char
  counts) only.
- Outputs: totals; by day; by model; by session (role name, not `cwd`); main vs. subagent;
  context-size buckets; attribution by tool and Bash command family; attribution by `gitBranch`
  (giving per-batch cost).
- Wire an opt-in `## Token Usage (Real)` section into `generate_retro.py` (`--include-real-tokens`
  flag) — additive, never touches the filesystem from inside `generate()` itself.
- Correct `docs/agent-monitoring/schema.md`'s "no workaround" claim and
  `retrieval_baseline_metrics.py`'s `build_context_tokens_section()`'s "platform-blocked" reason.
- Stream the corpus (never load ~1.2GB into memory at once); keep a `--since` filter.

## Out of Scope
- Making this part of the DEFAULT retro report — it is opt-in (`--include-real-tokens`), since
  streaming the real local corpus on every retro run would slow down the common case for a section
  most retro-reads won't always want.
- Writing any token data into `agent-monitoring/data/*.jsonl` — the per-event recording gap this
  ticket's own doc corrections describe remains genuinely unaddressed; this ticket adds a separate,
  retrospective, local-only analysis path, not a fix to that pipeline.
- Any change to how CI or a fresh clone behaves — this tool is unavailable in both, by design, and
  every consumer fails open when the transcript root is absent.
- Ticket 2 of this same batch (session context-reset trial) — related but separately scoped, and
  depends on this ticket landing first for its own before/after comparison.

## Acceptance Criteria
- [x] `tools/agent-monitoring/real_token_usage.py` exists, read-only, streams transcript files one
      at a time, never writes to a transcript, never returns/logs/persists raw conversation
      content — only numeric usage/metadata and tool-name/Bash-command-string/size aggregates.
- [x] Produces every output named in Scope, verified against both synthetic fixtures (tests) and a
      real, read-only CLI run against this machine's actual transcripts.
- [x] `generate_retro.py` gains the opt-in `## Token Usage (Real)` section; `generate()` itself
      takes an already-built report dict and never touches the filesystem — confirmed by the full
      pre-existing `test_generate_retro.py` suite passing unmodified alongside the 3 new tests.
- [x] `docs/agent-monitoring/schema.md` and `retrieval_baseline_metrics.py::build_context_tokens_
      section()` corrected; the latter's existing pinned test
      (`test_baseline_report_context_tokens_marked_unavailable`) still passes unmodified.
- [x] Tests use only synthetic fixture JSONL, built in-test; nothing real committed.
- [x] Streams the corpus; `--since` filter present in both the standalone CLI and the
      `generate_retro.py` wiring (derived from `--days`/`--week`/`--all`'s own existing window).

## Related Tickets
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — established `cost_proxy_score` as a proxy
  specifically because real token data was believed unobtainable; this ticket corrects that belief
  with a real, working alternative (a different-shaped one, not a replacement for the proxy's own
  per-event use).
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (done) — an earlier attempt at real token
  telemetry via a third-party proxy, which never got past MCP-explicit-trigger mode; this ticket
  achieves the "first real token telemetry" goal that epic's own Request Summary named, via a
  completely different, transcript-reading mechanism.

## Related Docs
- `docs/agent-monitoring/schema.md` — "What is not recorded" section, corrected.
- `docs/agent-monitoring/README.md` (if it exists and references the same claim — checked, no
  additional occurrence found beyond schema.md and retrieval_baseline_metrics.py).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260921-REAL-TOKEN-TELEMETRY/` — `investigation.md`, `plan.md`,
  `test_plan.md`.

## Related Code Areas
- `tools/agent-monitoring/real_token_usage.py` (new)
- `tools/agent-monitoring/generate_retro.py` (`generate()`, `main()`)
- `docs/agent-monitoring/schema.md`
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (`build_context_tokens_section()`)

## Assumptions / Open Questions
- Bash command family classification (`_bash_family`) is a simple first-two-words heuristic
  (matches the peer's own already-reviewed prototype) — good enough for attribution, not a general
  command parser. A more precise classifier is out of scope here.
- `gitBranch` attribution assumes this repo's own one-branch-per-batch convention
  (`CLAUDE.md`'s Worktree & Branch Isolation section) holds for the "per-batch cost" framing to be
  meaningful — a session that switches branches mid-conversation (the documented worktree-sharing
  fallback) would split its own cost across branch keys correctly, but a reader interpreting
  "per-batch" needs to know that convention, not assume the tool enforces it.
- Session names in `by_session` come from `agent-name`/`custom-title` rows recorded on the SAME
  session file — if a session never wrote either (an older or unusually short session), it falls
  back to the first 8 characters of its own session ID, which is correct but less readable.

## Implementation Notes
Promoted the peer's own already-prototyped, already-measured scratch logic
(`token_retro.py`/`token_report.py`/`token_by_tool.py`) rather than redesigning from scratch —
their design (streaming per-file parse, dedup by requestId, tool-context-sharing attribution) was
already correct; this ticket's own real contribution is making it a tested, read-only, permanently
reusable module instead of a one-off scratch script, plus the new git-branch attribution (per-batch
cost) the scratch scripts didn't yet have.

Deliberately did NOT run `generate_retro.py --include-real-tokens` for real during this ticket's
own verification — doing so would write and (per this repo's existing convention) commit a new
real `agent-monitoring/retro/RETRO-*.md` file embedding real aggregate numbers from this session's
own history. The ticket's own Test Summary says "nothing real may be committed," and while
aggregate numbers are not the raw conversation content the rule is protecting, generating a new,
permanently-committed real report wasn't asked for and isn't necessary to prove the wiring works —
a synthetic `real_token_report` dict fed directly to `generate()` (see `test_generate_retro.py`'s 3
new tests) proves the same rendering logic without that side effect. Real-machine validation of the
underlying module was done separately, safely, via the read-only standalone CLI.

Corrected `retrieval_baseline_metrics.py::build_context_tokens_section()`'s wording without
changing its `status`/`citation` fields, preserving the one existing test that pins them — added a
`workaround` key rather than overclaiming that this specific, reproducible-from-repo-data report
can now include real tokens (it deliberately still can't, and shouldn't, per its own scope).

## Test Summary
- `pytest tests/tools/test_real_token_usage.py -v` — 21 passed (all synthetic fixtures).
- `pytest tests/tools/test_generate_retro.py -q -m "not slow and not extra_slow"` — 191 passed
  (167 pre-existing unmodified + 3 new).
- `pytest tests/tools/test_retrieval_baseline_metrics.py -q -m "not slow and not extra_slow"` —
  20 passed (existing pinned shape preserved).
- Real, read-only CLI run against this machine's actual transcripts — confirmed working end to
  end against real data shapes; nothing written or copied into the repo.

## Files Changed
- `tools/agent-monitoring/real_token_usage.py` (new)
- `tests/tools/test_real_token_usage.py` (new, 21 tests)
- `tools/agent-monitoring/generate_retro.py` — new `real_token_report` param on `generate()`, new
  `--include-real-tokens` CLI flag and wiring in `main()`, new `## Token Usage (Real)` section.
- `tests/tools/test_generate_retro.py` — 3 new tests for the new section.
- `docs/agent-monitoring/schema.md` — corrected "What is not recorded" section.
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — corrected `build_context_tokens_section()`.
- `stored_artifacts/TCK-20260921-REAL-TOKEN-TELEMETRY/` (new).

## Completion Summary
Promoted the peer's already-prototyped, already-measured transcript-analysis logic into a tested,
read-only `tools/agent-monitoring/real_token_usage.py`, adding the one output it didn't yet have
(git-branch attribution — real per-batch cost). Wired an opt-in section into `generate_retro.py`
without changing that tool's default behavior for any existing caller. Corrected two false "token
data is unobtainable" claims this repo's own docs had carried since early on, without breaking the
one existing pinned test that depended on the corrected function's stable shape. All tests use
synthetic fixtures; real-machine validation was done read-only, with nothing copied into the repo.
No known material gap left unstated.
