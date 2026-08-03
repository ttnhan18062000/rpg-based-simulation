# Implementation Sequence — context-efficient-retrieval

Epic: `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`. Source: `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`. Scoped via `/create-tickets` to Phase 0-1 of the source doc's "Sequenced Future Epic" only — see `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md` for why Phase 2 onward (retrieval contract, cache implementation, observability events, shadow packets, workflow adoption) is deliberately not ticketed yet.

## Order

1. `TCK-20260728-PHASE0-PREREQ-CONFIRMATION` (hotfix — no deps in this batch)
2. `TCK-20260728-RETRIEVAL-BASELINE-METRICS` (standard — no hard dep on ticket 1, but its own report is more meaningful once the prerequisite is confirmed)
3. `TCK-20260728-EVAL-FIXTURE-REPAIR` (standard — fully independent; different subsystem, no shared files with 1 or 2)

## Why This Order Matters

Not a strict topological dependency chain — 2 and 3 do not read any output ticket 1 produces.
The ordering is a **reading-priority** recommendation: ticket 1 answers "is the epic's own
foundational assumption (Phase 0 prerequisite) actually true," which is worth confirming before
sinking effort into 2 (baseline measurement) or 3 (eval fixtures) in case it surfaces a real gap.
If a gate failure or scheduling reason makes reordering desirable, 2 and 3 are safe to run before
or in parallel with 1.

## Known Finding, Deliberately Not in This Batch's Scope

Ticket 1's own investigation found that `tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md`
still carries `status: active` / `phase: open` / body `## Status: OPEN` in its frontmatter and body,
despite being fully complete (Completion Summary present, recorded as `DONE` in
`tickets/working_log.csv`) — the only file among ~1096 in `tickets/done/` missing `phase: done`.
This is a real, separately-tracked doc-hygiene defect, not part of any ticket in this batch — see
ticket 1's own Out of Scope section. Fix as its own quick hotfix when convenient.
