---
status: active
layer: ai
authority: P2
audience: developer
ticket_id: TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME
phase: backlog
date: 2026-07-10
tags: [ai, agent-monitoring, determinism]
---

# TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME

## Title
Port .claude/workflows/*.js to real runtime execution instead of LLM narration (BACKLOG — future improvement, not actively blocked-and-waiting)

## Status
BACKLOG

## Tier
standard (once actionable)

## Type
refactor

## Priority
P2 (future improvement — not scheduled)

## Request Summary
Every `.claude/skills/*/SKILL.md` file explicitly states "the Workflow tool is not available" in
this harness, meaning `.claude/workflows/*.js` files are never executed by a real JS engine — an LLM
reads them and manually translates phases into tool calls each run, with no runtime enforcement that
the translation is complete or correctly ordered. The long-horizon fix is porting these files to run
under a real execution surface instead of being narrated by an LLM.

**Re-investigated twice in the same session (2026-07-11, ~03:12 and ~07:00)** — both times
independently re-confirming the blocking condition still holds, with zero drift between checks:
- Textual: all 5 relevant `SKILL.md` files still say "Do not call the Workflow tool — it is not available."
- Empirical: a live `ToolSearch` probe from inside this exact harness/session — including a direct
  exact-name lookup (`select:Workflow`) — found **no matching tool**. There is no `Workflow` tool or
  `tool_runner`-equivalent construct available inside this Claude Code CLI session.

**Decision (2026-07-11): moved from `tickets/inprogress/` (Status: BLOCKED) to
`tickets/backlogs/` (Status: BACKLOG).** This is a deliberate reframing, not a downgrade of intent:
"BLOCKED" implied active work waiting on an external event; in practice nobody can schedule or
predict that event, so the ticket was sitting idle rather than genuinely paused. "BACKLOG" more
accurately reflects: a real, well-understood future improvement, deliberately not competing for
sprint attention against the current incremental strategy (see `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md`'s Resolution section for the full reasoning) — not "waiting for a phone call," but "known, valuable, not now."

**New finding — a concrete unblock path exists, just not inside this harness.** Research into the
Claude API/Agent SDK ecosystem (via the `claude-api` skill's reference docs) surfaced that among the
four ways to build a Claude-powered agent, the **Claude Agent SDK** (`claude-agent-sdk` /
`@anthropic-ai/claude-agent-sdk` — described in its own docs as "Claude Code packaged as a library")
is architecturally exactly what this ticket's long-horizon idea describes: a real program that runs
the full agent loop, built-in tools, context management, hooks, subagents, and sessions
deterministically, callable via `query(prompt, options)`. This is **not** a capability that will
appear inside the current interactive Claude Code CLI session — pursuing it means designing, building,
and maintaining a **separate standalone program** (Python or TypeScript) outside this harness that
reimplements `.claude/workflows/*.js`'s phase sequencing and gate branching as real code, with
`Agent()`-style subagent calls as the only remaining LLM-judgment surface. That is a genuine,
uncertain-ROI engineering project — not a platform capability to wait for passively anymore, but a
build to actively choose, if and when it's worth it.

## Scope
If/when this is picked up from the backlog:
- Port `.claude/workflows/*.js` phase sequencing to run as actual code — either under a genuine
  in-harness `Workflow`/`tool_runner` surface (if one is ever added to Claude Code) or, more concretely
  per the finding above, as a standalone program built on the Claude Agent SDK.
- Port gate branching (e.g. Verify/Parity gate checks) to real runtime-executed control flow.
- Port `writeMonitoring`/bookkeeping calls (run entry, event entries) to deterministic runtime
  execution rather than LLM-narrated bash snippets.
- Leave `Agent()`-style subagent calls as the only remaining LLM-judgment surface in the workflow.
- Re-verify the blocking condition (or lack thereof) fresh at the start of whatever future
  Investigate phase picks this up — do not assume either this ticket's text or the two prior
  confirmations still hold; the empirical `ToolSearch` check is cheap and should be repeated, not
  trusted from memory.

## Out of Scope
- The near-horizon workflow-meta-conformance check — already shipped as
  `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` (DONE), not blocked on this ticket.
- Any change to sub-agent-level prompts or the sub-agent bookkeeping-determinism fix — that was
  `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`'s layer (DONE), not this one's.
- Any speculative implementation against a hypothetical in-harness execution surface before one is
  confirmed to exist — the empirical check must come first, every time this is revisited.
- Committing to the Claude Agent SDK rewrite path without a fresh cost/benefit decision at pickup
  time — this ticket records the path exists, it does not pre-approve building it.

## Acceptance Criteria
- [ ] (backlog) Confirm, fresh, whether a real Workflow-tool/tool_runner execution surface has
      become available *inside this harness* — this remains the first check, not a code change.
- [ ] (backlog, alternative path) If pursuing the Claude Agent SDK route instead: a scoping decision
      on which of the 11 `.claude/workflows/*.js` files to port (all of them, or just the 5
      skill-backed ones — `implement-ticket`, `implement-epic`, `create-tickets`, plus whichever
      others gain a `SKILL.md` wrapper by then) is made explicitly, not assumed.
- [ ] (provisional, contingent on either path above) `.claude/workflows/implement-ticket.js` ported
      to real executable code, with phase sequencing and gate branching no longer narrated by an LLM.

## Related Tickets
- TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC (parent — DONE, archived to
  `tickets/done/workflow-execution-determinism/`)
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK (sibling — DONE, `tickets/done/TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK.md`)
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC (related but distinct layer — sub-agent
  mechanical-step reliability, not orchestrator-narration; DONE, archived to
  `tickets/done/agent-bookkeeping-determinism/`)
- TCK-20260710-EPIC-SCOPE-ORPHAN-FIX / TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK (DONE — both
  surfaced during this session's reflection as evidence the current narrate+gate strategy is working:
  each ticket's own Verify gate caught the narrating LLM omitting a required `docs/` update before
  either reached `done`)
- TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE (done; prior work touching the create-tickets
  skill's now-stale "invoke the Workflow tool" instruction — related context, not a duplicate)

## Related Docs
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` (primary source — see its
  Resolution section for the full decision record and reasoning)
- `.claude/skills/implement-ticket/SKILL.md` (source of the "Workflow tool is not available"
  statement, still accurate as of the second 2026-07-11 confirmation)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME/` — investigation.md (includes both the
  first-pass and "Second Independent Confirmation" sections), plan.md (documents why no ordered
  implementation steps could be given while blocked), test_plan.md.

## Related Code Areas
- `.claude/workflows/*.js`
- `.claude/skills/*/SKILL.md`

## Assumptions / Open Questions
- Is a real `Workflow`/tool-runner execution surface plausible on any roadmap for this harness, or is
  "an LLM narrates a `.js` spec into tool calls" the permanent shape of this system? Still genuinely
  unknown from inside this repo after two independent empirical checks — re-check fresh at pickup,
  don't assume either answer.
- If the Claude Agent SDK path is chosen instead: is it worth building and maintaining a second,
  parallel orchestration system (the SDK-based standalone program) alongside the existing
  narrated `.claude/workflows/*.js` files, or would it fully replace them? Not decided here —
  a real design question for whoever picks this up.
- `layer: ai` retained from the original ticket (Claude agent-orchestration tooling, not gameplay
  AI/cognition, per this repo's tag registry convention).

## Implementation Notes
Not started — this is a backlog item, not in-progress work.

## Test Summary
N/A — no implementation exists yet.

## Files Changed
N/A — no implementation exists yet.

## Completion Summary
N/A — not complete; this is a backlog item pending a future decision to pick it up.
