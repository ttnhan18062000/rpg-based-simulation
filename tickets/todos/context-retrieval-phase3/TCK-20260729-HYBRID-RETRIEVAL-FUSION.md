---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-HYBRID-RETRIEVAL-FUSION
phase: open
date: 2026-07-28
tags: [ai, debugging, testing]
---

# TCK-20260729-HYBRID-RETRIEVAL-FUSION

## Title
Hybrid dense+lexical retrieval fusion with metadata filtering

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a query router that retrieves a bounded candidate set independently from a dense channel (tools/knowledge_search.py embeddings) and a lexical channel (BM25), unions the two, and combines them with reciprocal-rank fusion (RRF), with metadata filters applied before context assembly using the field schema fixed by Phase 2's context-packet-contract decision doc. This is motivated by a confirmed live bug: both tools/knowledge_search.py's cmd_query() and tools/search_mcp.py's _run_search() currently compute BM25 scores only over candidates that already survived the dense-channel ANN cut, silently dropping lexical-only exact matches outside that cut for every agent's search_docs call today, not just future work. A lightweight re-ranker beyond fusion+metadata is explicitly out of scope.

## Scope
- Build a new fusion module/helper implementing bounded independent dense-channel and lexical-channel candidate retrieval, union by doc/chunk id, and RRF scoring (sum of 1/(k+rank)).
- Fix the confirmed dense-candidate-gating bug in BOTH tools/knowledge_search.py's cmd_query() (lines ~992-1038) and tools/search_mcp.py's _run_search() (lines ~73-142) -- do not fix only one call site; route both through the new shared fusion helper if feasible.
- Apply metadata filters (per context_packet_contract.md's field schema) before RRF ranking, excluding non-matching candidates from fusion entirely.
- Preserve existing --mode vector/--mode keyword code paths unmodified.

## Out of Scope
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.
- Conflating with eval_search.py's existing _reciprocal_rank() (an MRR@10 metric) -- new RRF fusion logic must be named/implemented distinctly.

## Acceptance Criteria
- [ ] Exact-term query outside dense candidate_k now surfaces via the lexical channel (regression test for the confirmed bug).
- [ ] Dense and lexical channels independently retrieve bounded top-N, unioned by doc/chunk id, ranked via RRF (score = sum of 1/(k+rank)), not the current linear-weighted formula.
- [ ] Metadata filter excludes non-matching candidates before RRF ranking.
- [ ] Existing --mode vector/--mode keyword paths and their tests continue passing unmodified.

## Related Tickets
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
- TCK-20260612-LOCAL-CTX-EVAL
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/ai/default_packet_scenarios_decision.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/knowledge_search.py
- tools/search_mcp.py
- tools/eval_search.py
- tests/tools/test_knowledge_search.py
- tests/tools/test_search_mcp.py
- tests/tools/test_eval_search.py
- expected: tools/hybrid_retrieval.py
- expected: tests/tools/test_hybrid_retrieval.py

## Assumptions / Open Questions
- The confirmed live bug affects every agent's search_docs call today via tools/search_mcp.py, not just a hypothetical future scenario.
- eval_search.py already defines a function named _reciprocal_rank() that computes MRR@10, not RRF fusion -- naming collision must be avoided in the new module's naming.
- Metadata filter fields (authority/status/provider/lifecycle/freshness) don't exist as columns in knowledge-index/knowledge.db today; this ticket will need a build-time join against docs/REGISTRY.yaml frontmatter or new schema columns -- exact mechanism is an open implementation decision for planning.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
