---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260709-CONCERN-INVESTIGATOR-AGENT
phase: open
date: 2026-07-09
tags: []
---

# TCK-20260709-CONCERN-INVESTIGATOR-AGENT

## Title
Add a dedicated, tool-scoped agent for create-tickets.js's pre-ticket Investigate phase

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`.claude/workflows/create-tickets.js`'s Investigate phase (the step that runs per-concern, before any ticket file exists, to gather file paths/constraints/AC signals feeding the Structure phase) currently dispatches `Agent(subagent_type: "general-purpose", ...)` with the full ~80-line context-scan-and-investigate protocol (semantic search → graphify → registry query → working_log grep → code read → test discovery → AC derivation → tier assessment) restated inline in every prompt. This was noticed while running the workflow by hand: five near-identical, long prompt blocks had to be authored to enforce the same mandatory ordering from `CLAUDE.md`'s Context Scan rule, with real risk that a future edit updates the protocol in one place (e.g. the `investigator` agent's own methodology) without the other (create-tickets.js's inline copy) staying in sync. Separately, `general-purpose` grants full `Edit`/`Write`/`Bash` access to a phase that should only be reading and returning structured findings — nothing in this phase is supposed to mutate repo files.

The existing `investigator` agent (`.claude/agents/investigator.md`) already encodes this exact discipline as its identity, but its contract doesn't fit here: it requires an existing `tickets/inprogress/{ticket_id}.md` and always writes `staging_artifacts/{ticket_id}/investigation.md` + `test_plan.md` to disk. create-tickets.js's Investigate phase runs *before* a ticket exists (it investigates a proposed "concern", not a ticket_id) and must return schema-validated JSON (`files_found`, `constraints`, `existing_tests`, `related_tickets`, `ac_signals`, `risks`, `is_duplicate`, `tier_recommendation`, `summary`) for the Structure phase to consume — not markdown files.

## Scope
- Add a new agent definition (e.g. `.claude/agents/concern-investigator.md`) that owns the create-tickets.js Investigate-phase methodology as its system prompt: mandatory `search_docs` → `graphify query` → `docs/REGISTRY.yaml` → `tickets/working_log.csv` → code read → test discovery → AC-signal derivation ordering, matching `CLAUDE.md`'s Context Scan rule
- Scope its tool access to read/search only (mirror the `Explore` agent's restriction pattern: no `Edit`, `Write`, or file-mutating tools) since this phase never needs to change repo state
- Define its input/output contract explicitly as concern-scoped and JSON-returning (not ticket-ID-scoped, not file-writing) so it's structurally distinct from `investigator` rather than a reuse of it
- Update `.claude/workflows/create-tickets.js`'s Investigate phase (`await pipeline(comprehension.concerns, (concern) => agent(..., { label: ..., schema: INVESTIGATION_SCHEMA }))`) to pass `agentType: 'concern-investigator'` and shrink the per-concern prompt down to the concern-specific parameters, since the general methodology now lives in the agent's own system prompt
- Document the new agent in `docs/ai/agents.md` alongside the existing Ticket Lifecycle Agents section

## Out of Scope
- Changing `investigator`'s existing contract, output files, or its use within `implement-ticket.js`'s standard-tier pipeline
- Any change to the Structure, Write, or Link phases of `create-tickets.js`
- Retroactively re-running create-tickets on any already-created ticket batch

## Acceptance Criteria
- [ ] `.claude/agents/concern-investigator.md` exists, contains the mandatory context-scan ordering (search_docs first, then graphify, then registry, then grep) as durable system-prompt content, and does not grant `Edit`/`Write`/`NotebookEdit` tool access
- [ ] `.claude/workflows/create-tickets.js`'s Investigate phase invokes `agentType: 'concern-investigator'` instead of the current unscoped `general-purpose` default, and its per-concern prompt template is reduced to concern-specific substitutions (no longer restating the full protocol inline)
- [ ] Running create-tickets end-to-end on a sample proposal still produces JSON matching `INVESTIGATION_SCHEMA` (files_found, constraints, existing_tests, related_tickets, ac_signals, risks, is_duplicate, duplicate_of, tier_recommendation, summary) — the schema contract is unchanged, only how the agent is dispatched changes
- [ ] `docs/ai/agents.md` documents `concern-investigator` under a clearly distinct heading from `investigator`, stating explicitly when to use each (existing ticket + file artifacts vs. pre-ticket concern + structured return)

## Related Tickets
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE
- TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
- TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL
- TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES
- TCK-20260709-REGISTRY-COUNT-STALE-DOCS
- TCK-20260704-CREATE-TICKETS-MONITORING

## Related Docs
- `docs/ai/agents.md`
- `.claude/agents/investigator.md`
- `.claude/workflows/create-tickets.js`
- `CLAUDE.md` (Context Scan Mandatory section)

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/workflows/create-tickets.js`
- `.claude/agents/investigator.md`
- `.claude/agents/architecture-reviewer.md` (reference example of a review-only, narrowly-scoped agent definition)

## Assumptions / Open Questions
- Assumes the project wants a distinct agent type rather than widening `investigator`'s contract to support two output modes — this was the explicit recommendation when the concern was raised, on single-responsibility and pipeline-safety grounds (don't risk the standard-tier ticket pipeline that already depends on `investigator`'s current file-writing behavior)
- Open question: should `concern-investigator` also be made available for direct/manual invocation outside `create-tickets.js` (e.g. ad hoc "investigate this idea before I write a ticket" use), or scoped strictly to the workflow's internal use? Left for planning to decide.
- This ticket originated from an observation made while manually executing `create-tickets.js`'s phases in a live session (not from a written proposal doc), rather than from a pre-existing bug report or user complaint — the "author's intent" is the investigator's own recommendation captured in conversation.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

