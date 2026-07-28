---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-CONTEXT-PACKET-SCHEMA
phase: open
date: 2026-07-28
tags: [ai, registry, schema]
---

# TCK-20260728-CONTEXT-PACKET-SCHEMA

## Title
Define Context-Packet Schema and Authority/Freshness Field Contract

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants a decision document that specifies the fields of a provider-neutral ContextPacket (and its ContextRequest) — packet_id, corpus_generation, retrieval_version, budget_requested/returned, included[] entries with source_id/kind/path/heading_or_symbol/hash/authority/freshness/score/inclusion_reason/excerpt_budget, excluded_summary[], and expansion_policy. This should resolve Open Decision 3 (which authority/freshness metadata is mandatory on a packet source, and how conflicting active documents are represented) and build on the existing docs/REGISTRY.yaml authority/status primitive rather than replacing it. This matters because Phase 3+ retrieval/cache work will build directly against whatever schema this doc fixes, so it needs to be settled before any implementation lands.

## Scope
- Author docs/engine/contracts/context_packet_contract.md (new) specifying ContextRequest fields (task_ref/ticket_id/free-text intent, provider, agent_role, workflow, phase, risk_tier, changed_paths, scenario, token_budget) and ContextPacket fields (packet_id, corpus_generation, retrieval_version, budget_requested, budget_returned, included[] with source_id/kind/path/heading_or_symbol/hash/authority/freshness/score/inclusion_reason/excerpt_budget, excluded_summary[], expansion_policy), verbatim from the idea doc's Proposed Architecture section 1.
- Resolve Open Decision 3 (mandatory authority/freshness metadata; representation of conflicting active documents) with a cited answer that builds on docs/REGISTRY.yaml's existing status/authority enums rather than inventing a parallel system.
- Give the doc frontmatter that passes tools/validate_frontmatter.py with a registered layer and pre-registered tags.
- Link the new contract doc from TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC as a Phase 2 deliverable.

## Out of Scope
- Any src/ or tools/ implementation of ContextPacket construction/serialization code.
- Phase 3 retrieval/cache implementation.
- Phase 4 observability events/dashboard work.
- Phase 5-6 shadow packets or workflow adoption.
- Force-resolving Open Decisions 1, 2, 4, 5, or 6.
- Replacing or modifying docs/REGISTRY.yaml's existing status/authority enum values.

## Acceptance Criteria
- [ ] New doc (expected: docs/engine/contracts/context_packet_contract.md) exists with frontmatter that passes tools/validate_frontmatter.py using a registered layer/tags.
- [ ] Doc documents ContextRequest fields and ContextPacket fields (as listed in scope) verbatim from the idea doc's Proposed Architecture section 1.
- [ ] Doc explicitly resolves Open Decision 3 with a cited answer building on REGISTRY.yaml's status/authority enums rather than inventing a parallel system.
- [ ] Ticket's Out of Scope excludes any src/tools/ implementation, retrieval/cache code (Phase 3), observability events (Phase 4), and workflow adoption (Phase 5-6).

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR
- TCK-20260721-MONITORING-WRITER-DECISION

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/parity_ledger/schema.json
- docs/engine/contracts/task_result_update_substrate_contract.md
- docs/ai/monitoring_writer_decision.md
- docs/REGISTRY.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/parity_ledger/schema.json
- docs/engine/contracts/task_result_update_substrate_contract.md
- docs/ai/monitoring_writer_decision.md
- docs/REGISTRY.yaml
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/todos/context-efficient-retrieval/SEQUENCE.md
- expected: docs/engine/contracts/context_packet_contract.md

## Assumptions / Open Questions
- No existing REGISTRY.yaml mechanism represents 'conflicting active documents' today; the doc must propose a doc-only resolution or explicitly flag this as an unresolved gap rather than silently inventing new registry machinery.
- The parent epic (TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC) remains open and covers Phase 0-1 only; this ticket is a Phase 2 child, not an epic-closing change.
- Open Decisions 5 and 6 are explicitly deferred to later phases and must not be force-resolved here.
- Tier is standard rather than hotfix because this doc establishes a durable schema/contract that Phase 3+ will build against, which is architecture-review-worthy even though the deliverable is doc-only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
