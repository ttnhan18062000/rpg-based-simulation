---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
phase: open
date: 2026-07-28
tags: []
---

# TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Title
Epic: Context-Efficient Agent Retrieval and Observability Initiative

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
Create a single epic-tier tracking ticket for the whole context-efficient agent retrieval and observability initiative. It is scope-only (no implementation), references the full 7-phase 'Sequenced Future Epic' sequence (item 0 Prerequisites plus phases 1-7) from the source doc as its own record, and lists all 6 Open Decisions from the source doc as unresolved items to be settled later.

## Scope
- Create epic-tier ticket tracking the context-efficient agent retrieval and observability initiative per docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- Record the full Sequenced Future Epic list (item 0 Prerequisites + phases 1-7) as this epic's own record, verbatim or by citation
- List all 6 Open Decisions from the source doc verbatim in Assumptions/Open Questions as unresolved
- Follow TCK-20260721-PROVIDER-AGNOSTIC-EPIC precedent for epic-tier scope-only wording

## Out of Scope
- No direct implementation of any phase (0-7)
- Does not authorize a new mandatory workflow gate
- Does not authorize a production monitoring-writer change
- Does not authorize a new external retrieval service
- Does not authorize adopting Qdrant/Postgres-pgvector/Neo4j/hosted RAG before measured need
- No child ticket creation performed inside this ticket itself

## Acceptance Criteria
- [ ] Epic's Scope section contains only tracking/sequencing wording, no implementation claimed
- [ ] Epic references source doc's full Sequenced Future Epic list (item 0 Prerequisites + phases 1-7) verbatim or by citation
- [ ] Assumptions/Open Questions section lists all 6 Open Decisions from source doc verbatim, marked unresolved
- [ ] Out of Scope explicitly excludes: new mandatory workflow gate, production monitoring-writer change, new external retrieval service, Qdrant/Postgres-pgvector/Neo4j/hosted RAG before measured need
- [ ] Ticket body ## Tier field is 'epic'; Related Code Areas is empty/none (scope-only)

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260702-OBSISO-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md
- tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md
- tickets/todos/obs-isolation/TCK-20260702-OBSISO-EPIC.md

## Related Stored Artifacts
None.

## Related Code Areas
- none (scope-only epic)

## Assumptions / Open Questions
- Need to confirm the Phase 6 deferred-from-provider-agnostic-epic 'stable monitoring path' precondition is not the same thing as this epic's own item 0 prerequisite — verification tracked via child ticket TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- Maturity banner in source doc marks this PROPOSED FUTURE EPIC — does not yet authorize new mandatory workflow gate/writer change/external retrieval service
- OPEN DECISION 1: Which scenarios and phases justify a default context packet, and what are their initial token budgets?
- OPEN DECISION 2: Which code/test relationships can be built deterministically from existing AST, import, test naming, and Graphify data before adding any semantic code model?
- OPEN DECISION 3: Which authority/freshness metadata should be mandatory for a packet source, and how should conflicting active documents be represented?
- OPEN DECISION 4: What retention and redaction policy applies to retrieval events and cache entries?
- OPEN DECISION 5: What sample size and thresholds are sufficient to promote a scenario from advisory to default behavior?
- OPEN DECISION 6: Should context packets be exposed as an MCP tool, a provider-adapter library, or both after the provider-neutral contract is implemented?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
