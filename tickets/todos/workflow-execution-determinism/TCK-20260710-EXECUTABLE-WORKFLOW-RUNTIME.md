---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME
phase: open
date: 2026-07-10
tags: [ai, agent-monitoring, determinism]
---

# TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME

## Title
Port .claude/workflows/*.js to real runtime execution instead of LLM narration (DRAFT — blocked on platform capability)

## Status
BLOCKED

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
**DRAFT — BLOCKED. This ticket is explicitly NOT actionable today; it exists to preserve the idea, not to be scheduled for implementation. Do not attempt to Plan or Implement this ticket until its blocking condition (a real workflow-execution surface) is confirmed available — re-verify that confirmation at the start of any future Investigate phase, don't assume it from this ticket's text alone.**

Source idea doc: `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` (see its "Long-horizon: execute, don't narrate" section).

Every `.claude/skills/*/SKILL.md` file explicitly states "the Workflow tool is not available" in this harness, meaning `.claude/workflows/*.js` files are never executed by a real JS engine — an LLM reads them and manually translates phases into tool calls each run, with no runtime enforcement that the translation is complete or correctly ordered. The long-horizon fix is porting these files to run under a real execution surface (a genuine Workflow tool, or an Agent SDK `tool_runner`-style loop) if/when one becomes available.

## Scope
As described in the idea doc's Long-horizon section, if/when a genuine workflow-execution surface becomes available in this harness:
- Port `.claude/workflows/*.js` phase sequencing to run as actual code executed by that runtime, not narrated by an LLM.
- Port gate branching (e.g. Verify/Parity gate checks) to real runtime-executed control flow.
- Port `writeMonitoring`/bookkeeping calls (run entry, event entries) to deterministic runtime execution rather than LLM-narrated bash snippets.
- Leave `Agent()` calls as the only remaining LLM-judgment surface in the workflow.

## Out of Scope
- The near-horizon workflow-meta-conformance check (separate draft ticket, `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`, created in parallel) — that one IS actionable now and must not be blocked on this one.
- Any change to sub-agent-level prompts or the sub-agent bookkeeping-determinism fix — that is `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`'s layer, not this one's.
- Any speculative implementation against a hypothetical execution surface before one is confirmed to exist.

## Acceptance Criteria
- [ ] (blocked) Confirm whether a real Workflow-tool/tool_runner execution surface has become available in this harness — this is the actual first step of any future work here, not a code change.
- [ ] (provisional, contingent on the above) `.claude/workflows/implement-ticket.js` ported to real executable code under that surface, with phase sequencing and gate branching no longer narrated by an LLM.

## Related Tickets
- TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC (parent — being created in parallel)
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK (sibling draft, NOT blocked, actionable independently)
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC (related but distinct layer — sub-agent mechanical-step reliability, not orchestrator-narration)
- TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE (done; prior work touching the create-tickets skill's now-stale "invoke the Workflow tool" instruction — related context, not a duplicate of this ticket's long-horizon scope)

## Related Docs
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` (primary source)
- `.claude/skills/implement-ticket/SKILL.md` (source of the "Workflow tool is not available" statement, line 26)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `.claude/workflows/*.js`
- `.claude/skills/*/SKILL.md`

## Assumptions / Open Questions
Carried forward verbatim from the idea doc's Open Questions section:
- Is a real `Workflow`/tool-runner execution surface plausible on any roadmap for this harness, or is "an LLM narrates a `.js` spec into tool calls" the permanent shape of this system? Genuinely unknown from inside this repo — this is explicitly unresolved and must be re-checked, not assumed, whenever this ticket is revisited.
- Should this be scoped as its own epic when scheduled (leaning yes, per the idea doc), given it operates one architectural layer above `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` — not decided unilaterally here.
- `layer: ai` was inferred from this being Claude agent-orchestration tooling (per this repo's tag registry note that `ai` means "the Claude agent system, not gameplay AI/cognition"), consistent with the idea doc's own frontmatter.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

