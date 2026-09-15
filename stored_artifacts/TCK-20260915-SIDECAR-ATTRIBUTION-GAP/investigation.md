---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-GAP
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260915-SIDECAR-ATTRIBUTION-GAP

## Re-derived baseline

Direct shard scan, last 14 days from now (a few hours later than the ticket's own 2026-09-01
snapshot, so a small drift from 23.7%/30.5% is expected and confirmed): **24.7%** of tool rows
(12,805 of 51,748) carry no `run_id`. Re-derive at implementation time, per this repo's own
convention — the corpus grows daily.

## The stated cause is stale — a real fix already landed for the exact mechanism named

The ticket's Request Summary cites `.claude/current_run` as "a single shared sidecar file across
all concurrent sessions ... confirmed live 2026-08-24" as the live cause. Reading
`tools/agent-monitoring/post_tool_hook.py` directly shows that exact defect was already fixed, the
same day it was found: `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` made the hook prefer a
per-session file (`.claude/current_run.<session_id>`) over the shared one, and
`TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION` made it write an explicit null-valued sentinel — not
fall back to the shared file — when no scoped file exists yet for that session. Both are real,
tested, and currently active code (confirmed by reading the hook's own logic, not assumed from the
ticket names). **The specific cross-session-contamination bug described is not the live cause of
today's 24.7%** — that mechanism means every unattributed row today is either a genuine "no active
ticket sidecar for this session" case, or something else entirely, not silent cross-session
misattribution.

## What IS live: classified, not assumed

**Uniform rate across tool types — rules out a tool-specific timing race.** Per-tool unattributed
rates: `Read` 20.9%, `Edit` 26.9%, `Write` 32.5%, `Bash` 24.6% — all within the same ~21–33% band
as the overall 24.7%. A sidecar-write-vs-tool-call race (sidecar written a few calls late/early)
would show a sharply elevated rate for whichever tool type sits nearest the sidecar boundary; it
doesn't. The gap is spread proportionally across all activity, consistent with entire STRETCHES of
session time lacking an active sidecar, not individual missed calls near a boundary.

**Direct sampling of unattributed `Edit`/`Write` rows shows real ticket-implementation work, not
noise.** 15 rows sampled at random from the 1,896 unattributed `Edit`/`Write` rows in the 14-day
window are ALL genuine ticket/source/test file edits: `tickets/inprogress/TCK-...`,
`src/worldassembly/resolv...`, `src/engine/pipeline_phas...`, `src/domains/combat_engag...`,
`tests/unit/domains/comba...`. **This rules out "it's all legitimate non-ticket interactive
calls."** A session editing real ticket source files is doing real, attributable-in-principle work
— the AC's own "legitimately has no run" category does not cover this class.

**Session-level breakdown**: of 10 distinct sessions active in the 14-day window, only 2 are 100%
unattributed (pure non-ticket work — legitimate). The other 8 show a MIX of attributed and
unattributed rows within the same session — 9,281 of the 12,805 unattributed rows (72%) come from
sessions that DID successfully attribute other rows elsewhere in their own history. This is the
shape of "this session did real ticket work some of the time, and lacked sidecar coverage the rest
of the time" — consistent with the hand-orchestration compliance gap CLAUDE.md's own text names
directly: *"Forgetting this is the single most common hand-orchestration gap."* A session
hand-translating `implement-ticket.js` across many phases, on a long or resumed ticket, missing
`writeSidecar()` before some subset of phases, produces exactly this mixed pattern.

**A second, structurally distinct candidate mechanism, disclosed but not confirmed to the same
level of certainty**: `Agent()`-dispatched subagents (the formal pipeline's own `investigator`/
`planner`/`implementer`/... calls) may run under a session identity distinct from their
orchestrating session. If so, a subagent's own tool calls would check
`.claude/current_run.<subagent_session_id>` — a file the orchestrator's `writeSidecar()` call never
wrote (it wrote `.claude/current_run.<orchestrator_session_id>`) — and would be null-sentinel'd
100% of the time, regardless of how carefully the orchestrator followed the sidecar convention.
This is plausible and would explain a real, systemic share of the gap for the FORMAL pipeline
specifically (as opposed to hand-orchestration), but confirming it requires tracing a specific
`Agent()` dispatch's own session_id against its parent's — out of this ticket's practical scope to
fully resolve; recorded as an open mechanism for `TCK-20260915-MONITORING-ANOMALY-VALIDATOR`
(the capstone) or a follow-up to investigate with harness-level access this ticket doesn't have.

## Link to `TCK-20260915-TOOL-CALL-COUNT-MISMATCH` — confirmed, not assumed

Read `tools/agent-monitoring/record_events.py::compute_tool_stats()` directly: `cost_proxy_score`
is computed by grouping REAL `tools.jsonl` rows by `(run_id, seq)` and matching them to each
event's own `(run_id, seq)`. **A tool row with no `run_id` can never be matched to any event, by
construction** — the exact same unattributed rows measured above are what drives both this
ticket's 30.5% `cost_proxy_score` coverage gap AND (very likely) ticket 3's `tool_call_count`
mismatches, since both read from the identical `(run_id, seq)` grouping over the identical
`tools.jsonl` corpus. **Confirmed: shared cause, not merely probable** — ticket 3's own
investigation should build on this rather than re-deriving it, and should focus on whether there
is anything BEYOND this shared cause (e.g. a `seq` off-by-one, not just missing `run_id`).

## Classification answer (AC #1)

Not cleanly separable into a bright-line "legitimately unattributed" vs. "lost attribution" split
by row — the evidence (uniform per-tool rate, real-file-edit content, mixed-session pattern) points
to the gap being **dominated by real, in-principle-attributable ticket work that lacks sidecar
coverage for structural/compliance reasons**, not by legitimate non-ticket interactive calls. The
2 fully-unattributed sessions (representing a modest, genuinely-legitimate floor) are the cleanest
"legitimately has no run" instances found; the rest of the volume is best described as "real work,
missing attribution" rather than confidently split further without deeper per-session tracing this
ticket does not have the tooling to do cheaply.
