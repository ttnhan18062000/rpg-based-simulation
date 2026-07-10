---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC
phase: open
date: 2026-07-10
tags: [ai, agent-monitoring, determinism]
---

# TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC

## Title
The orchestrator itself is narrated, not executed — epic tracking 2 draft child tickets

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
This epic tracks `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md`
(raised 2026-07-10, maturity "IDEA — not scheduled"). The idea doc observes that the sibling
epic (`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`) fixes sub-agent-layer mechanical-step
reliability (e.g. moving `.claude/current_run` sidecar registration out of agent-prompt text and
into orchestrator-side `bash()` calls), but that fix implicitly assumes the orchestrator itself is
deterministic — a real program executing real code. It is not: every
`.claude/skills/{implement-ticket,implement-epic,create-tickets}/SKILL.md` states "Do not call the
Workflow tool — it is not available. Execute the workflow directly," meaning `.claude/workflows/*.js`
is prose-shaped pseudocode narrated by an LLM into tool calls once per invocation, with nothing
enforcing the translation is complete or in the right order except the narrating LLM's own diligence.
The idea doc cites two live reproductions this session of that exact failure mode (a Step 0b
sidecar-registration omission across 5 agent prompts, and a `done-checker` catching a skipped
`## Test Summary`/`## Files Changed` write on the orchestrating LLM's own first Verify pass), plus
the fact that no automated test harness exists for `.claude/workflows/*.js` at all — a direct
structural consequence of the workflow not being real, testable code.

This epic tracks **2 DRAFT child tickets**, both light-scoped directly from the idea doc's two
proposed responses (a near-horizon static check and a long-horizon runtime-porting aspiration). Per
CLAUDE.md's Tier Routing table, `epic` tier is Scope only — no direct implementation happens here.
**Both children are drafts, not investigated tickets**: no deep per-concern investigation has been
done yet for either. That is explicitly deferred to each child ticket's own future Investigate phase,
which must run and resolve the idea doc's relevant Open Questions before any Plan/Implement work
begins on either child.

## Scope
Track the following 2 draft child tickets, to be created next via the create-tickets workflow:

1. **Workflow-meta-conformance static check** (near-horizon, actionable now). A static verifier
   (proposed: `tools/gate_checks/workflow_meta_conformance.py`) that, given a completed run's
   `run_id`, parses each workflow's declared `meta.phases` array (from the `.js` source) and
   cross-references it against that run's actual `agent-monitoring/events.jsonl` entries, flagging
   any declared phase with zero matching events — a phase the narrating LLM silently skipped
   entirely. Direct structural analog of `tools/gate_checks/parity_updater_static.py`'s
   `cross_reference_touched` (files→ledger there, phases→events here).
2. **Executable-workflow-runtime aspiration** (long-horizon, explicitly NOT actionable today per the
   idea doc — blocked on a platform capability, "the Workflow tool," that every relevant SKILL.md
   file says "is not available" in this harness). Port `.claude/workflows/*.js` to run under a real
   execution runtime (a genuine `Workflow` tool, or a Claude Agent SDK `tool_runner`-style agentic
   loop) instead of being narrated by an LLM into tool calls — phase sequencing, gate branching, and
   `writeMonitoring` calls executed deterministically by the runtime, with sub-agent `Agent()` calls
   as the only place genuine LLM judgment enters the loop.

## Out of Scope
- Do not fold this into `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` — the idea doc explicitly
  frames this as a distinct architectural layer (orchestrator-as-narrator vs. sub-agent-as-worker),
  "not a child of it, and not folded into its scope." Keep the two epics separate.
- Do not implement anything directly in this epic — epic tier is Scope only.
- Do not attempt to build or request access to a real `Workflow`/tool-runner execution surface as
  part of scoping child ticket 2 — the idea doc is explicit that this is not actionable today and is
  recorded so intent isn't lost, not as a task to schedule now.
- Do not pre-decide, in this epic, whether a missing-phase-event finding from child ticket 1 should
  be advisory or a hard Finalize block — that is one of the idea doc's open questions, deferred to
  child ticket 1's own Investigate/Plan phases.

## Acceptance Criteria
- Both child tickets exist under `tickets/todos/workflow-execution-determinism/` (or promoted to
  `tickets/inprogress/` when work begins) and are linked from this epic's Related Tickets section.
- Each child ticket's own future Investigate phase, when eventually run, resolves the idea doc's
  Open Questions relevant to that child (child 1: advisory-vs-hard-block for missing-phase-event
  findings; child 2 and the epic-scoping question apply to this epic/child-2 pairing) before any
  Plan/Implement work begins on that child.
- No implementation code or tests are introduced by this epic ticket itself (epic tier is Scope
  only — verified by `Files Changed` being empty at Finalize).

## Related Tickets
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK (draft — actionable near-horizon check)
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (draft — blocked, long-horizon aspiration)

Related (distinct layer, not a duplicate): `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`
(`tickets/todos/agent-bookkeeping-determinism/TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC.md`).

## Related Docs
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` — primary source idea doc.
- `docs/ai/ticket-lifecycle.md` — documents the current `implement-ticket` workflow's phase-by-phase
  behavior, including `writeMonitoring`'s non-fatal write-failure handling.
- `docs/ai/workflows.md` — documents workflow invocation via the (currently narrated, not executed)
  `Workflow({...})` construct and the "Manual Execution (Without the Workflow)" fallback path.
- `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` — sibling idea doc this one
  explicitly distinguishes itself from.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `.claude/workflows/*.js` (e.g. `implement-ticket.js`, `implement-epic.js`, `create-tickets.js`) —
  each exports a `meta.phases` array; the declarative source of truth child ticket 1 would read.
- `.claude/skills/*/SKILL.md` — each contains the "Do not call the Workflow tool — it is not
  available. Execute the workflow directly" instruction that motivates this epic.
- `tools/gate_checks/` — home of the existing static-verifier precedents
  (`parity_updater_static.py`'s `cross_reference_touched`, `done_checker_static.py`'s
  `run_finalize_selfcheck`) that child ticket 1 would mirror.
- `agent-monitoring/events.jsonl` — the actual-execution data source child ticket 1's
  cross-reference would read against `meta.phases`.

## Assumptions / Open Questions
Carried forward verbatim from the idea doc's Open Questions section — **not yet resolved**, and
explicitly deferred to each child ticket's own future investigation. This epic and both its children
are drafts, not investigated tickets:

1. Is a real `Workflow`/tool-runner execution surface plausible on any roadmap for this harness, or
   is "an LLM narrates a `.js` spec into tool calls" the permanent shape of this system? Genuinely
   unknown from inside this repo — child ticket 2's long-horizon framing is written to survive
   either answer without needing to be rewritten.
2. Should a missing-phase-event finding from the proposed conformance check (child ticket 1) be
   advisory (a nudge, like `retro_nudge_hook.py`) or a hard block at Finalize? CLAUDE.md's Hard Rule
   that "monitoring write failure must never fail the workflow" governs *monitoring writes*; a
   silently-skipped phase is arguably a workflow-integrity failure, not a monitoring-write failure —
   this distinction should be decided deliberately in child ticket 1's own Investigate/Plan phases,
   not defaulted either way here.
3. Should this be scoped as its own epic when scheduled, given it operates one architectural layer
   above `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` (orchestrator-as-narrator vs.
   sub-agent-as-worker), or treated as a fourth child of that same epic? This epic answers that
   question as "own epic" by existing as such — named here as inherited context, not re-litigated.

If any of these three assumptions turn out wrong once a child ticket's Investigate phase actually
runs, the scope recorded here should be treated as provisional and revised rather than assumed
still valid.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
