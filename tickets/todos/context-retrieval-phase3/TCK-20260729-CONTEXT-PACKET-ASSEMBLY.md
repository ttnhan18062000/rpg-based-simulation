---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-CONTEXT-PACKET-ASSEMBLY
phase: open
date: 2026-07-28
tags: [ai, schema]
---

# TCK-20260729-CONTEXT-PACKET-ASSEMBLY

## Title
Assemble real ContextPacket from fused/cached retrieval results

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Assemble an actual ContextPacket per the Phase 2 schema from C1's fused retrieval results and C3's cached results, with real included[]/excluded_summary[] population, proving the schema is buildable from real data -- read-only, standalone, never wired into any workflow. Because this ticket consumes the actual return-value shapes of the fusion module (C1) and the cache module (C3), neither of which exists yet, it is hard-blocked on both and must be sequenced strictly last in this batch.

## Scope
- Build a new ContextPacket assembler module that consumes C1's fused retrieval results and C3's cached results and populates included[]/excluded_summary[] per the Phase 2 schema.
- Implement Decision A: code_symbol/test/graphify_node/in-progress-ticket-body kinds get authority=freshness='unrated' sentinel, never defaulted to P2/historical; parity_ledger_entry kind uses its own priority/status fields, never coerced into the REGISTRY enum.
- Implement Decision B: when two included[] entries are both active/authoritative on the same subject, both must be included (never silently dropped), ranked by authority then last_verified, with the lower-ranked entry's inclusion_reason naming the superseding entry.
- Construct/extend real test fixtures mixing REGISTRY-backed and non-registry-backed source kinds, since no such fixture currently exists.
- Stub expansion_policy as a clearly-marked placeholder field, not invented escalation semantics, since Open Decisions 5/6 remain deferred.
- Keep the module read-only and standalone -- must NOT be wired into or referenced from any .claude/workflows/*.js file.

## Out of Scope
- Implementing C1's fusion logic or C3's cache logic itself -- this ticket consumes their output only, does not reimplement them.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6 (expansion_policy stays a stub).

## Acceptance Criteria
- [ ] A candidate set with a code_symbol entry with no REGISTRY entry produces an included[] item with authority=="unrated" and freshness=="unrated".
- [ ] Two candidate docs both status:active on the same subject (one P0, one P1) produce BOTH in included[]; the P1 entry's inclusion_reason names the P0 entry's source_id as superseding.
- [ ] Every included[] entry has exactly the 10 contract fields; every excluded_summary[] entry has exactly the 4 contract fields; unit-tested against a fixture.
- [ ] Assembled packet never contains raw prompt/chunk text in any field.
- [ ] Module is not imported by/referenced from any .claude/workflows/ file; grep-based regression test asserts zero references.

## Related Tickets
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260729-HYBRID-RETRIEVAL-FUSION
- TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/knowledge_search.py
- tools/agent-monitoring/build_index.py
- tools/eval_search.py
- tools/eval/queries.json
- tools/validate_frontmatter.py
- tests/tools/test_knowledge_search.py
- tests/tools/test_eval_search.py
- expected: tools/context_packet_assembler.py
- expected: tests/tools/test_context_packet_assembler.py

## Assumptions / Open Questions
- Hard blocking dependency on C1 (fusion) and C3 (cache) -- neither exists yet at ticket-creation time; this ticket must be sequenced strictly after both land, per SEQUENCE.md ordering.
- Decision B's tie-break rule is advisory/doc-only guidance today; this ticket's test suite is the only place it becomes concretely verifiable -- ACs must test it directly or the Phase 2 schema resolution remains unproven by real code.
- expansion_policy is a listed ContextPacket field with no resolved definition anywhere (Open Decisions 5/6 both deferred) -- must stub with a clearly-marked placeholder.
- No fixture corpus currently mixes REGISTRY-backed and non-registry-backed source kinds -- nontrivial new fixture-authoring work is required.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
