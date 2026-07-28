---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-DETERMINISTIC-CODE-INDEX
phase: open
date: 2026-07-29
tags: [ai, investigation]
---

# TCK-20260729-DETERMINISTIC-CODE-INDEX

## Title
Deterministic-only code/test symbol index

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend retrieval to cover code/test symbols using ONLY relationship types the Phase 2 decision doc (docs/ai/code_test_index_boundaries_decision.md) confirmed are deterministic (graphify's AST edges) -- no new semantic/LLM code model. Investigation found the decision doc's per-relation-type claim (that all Part A relation types carry confidence_score=1.0) is factually wrong at the per-edge level: live graphify-out/graph.json shows 'uses' edges 100% INFERRED and 'calls' 42% INFERRED. This ticket must therefore filter admission on each edge's own confidence_score field, not on relation-type name alone, to actually deliver the deterministic-only guarantee the decision doc intended.

## Scope
- Build a new deterministic code/test symbol index module that admits an edge only if its relation type is in the Part A allowlist AND the edge's own confidence_score field == 'EXTRACTED'.
- Explicitly correct for the Phase 2 decision doc's per-relation-type claim, which investigation found factually wrong at the per-edge level (uses=100% INFERRED, calls=42% INFERRED).
- Explicitly decide and state whether to formalize test-scoper's code-to-test mapping into this index, or leave 'associated tests' as a stated/flagged gap -- do not silently leave it empty.
- Index symbols/relationships, not whole-file chunks; bounded-hop neighbor queries only, never inject a full community unless architectural traversal is explicitly requested.
- Pin graphifyy==0.6.7 in requirements given it's currently unpinned and externally pip-installed.

## Out of Scope
- Any Part B (LLM-derived) graphify relation type.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.

## Acceptance Criteria
- [ ] Index builder admits an edge ONLY if relation is in the Part A allowlist AND the edge's own confidence_score == 'EXTRACTED' (not just relation-name membership); unit test asserts zero INFERRED edges appear in output.
- [ ] Rebuilding the index twice from the same graph.json produces byte-identical output.
- [ ] Each record exposes module/symbol/docstring/owned component/associated-tests, populated from a real mapping OR explicitly flagged as an unresolved gap, never silently empty.
- [ ] Querying by a changed src/ file path returns only bounded-hop neighbors, never a full community, unless the caller explicitly requests architectural traversal.

## Related Tickets
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Related Docs
- docs/ai/code_test_index_boundaries_decision.md
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- graphify-out/graph.json
- graphify-out/GRAPH_REPORT.md
- graphify-out/manifest.json
- tools/knowledge_search.py
- tools/eval_search.py
- tools/eval/queries.json
- tests/tools/test_knowledge_search.py
- tests/tools/test_build_index.py
- tests/tools/test_eval_search.py
- expected: tools/code_test_index.py
- expected: tests/tools/test_code_test_index.py

## Assumptions / Open Questions
- The Phase 2 decision doc's claim that all Part A relation types carry confidence_score=1.0 is contradicted by live graphify-out/graph.json data (uses=100% INFERRED, calls=42% INFERRED); this ticket's filtering must use per-edge confidence, not the doc's per-type claim.
- graph.json also contains 'method' (100% EXTRACTED) and 'inherits' (100% EXTRACTED) relation types not listed in the decision doc's table at all -- real deterministic data outside documented scope, to be included only if planning confirms they fit Part A's intent.
- graphifyy pip package is not currently pinned in requirements; a future upstream upgrade could silently change vocabulary/confidence semantics.
- Several allowlisted relation types have zero occurrences in this repo's graph currently -- not a bug, tests should not assume they'll ever populate.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
