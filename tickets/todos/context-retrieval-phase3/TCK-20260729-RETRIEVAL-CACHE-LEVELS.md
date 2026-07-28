---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-CACHE-LEVELS
phase: open
date: 2026-07-29
tags: [ai, observability]
---

# TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Title
3-level SQLite retrieval cache with invalidation tests

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement 3 independently invalidatable caches (embedding/index, query-result, context-packet) per the idea doc's Cache design table, using SQLite, following the already-resolved retention/redaction policy's category names (retrieval_index_cache/retrieval_query_cache/retrieval_packet_cache) and MAY/PROHIBITED field list. This is genuinely new code -- no cache implementation exists anywhere in the repo today -- and must not be built as an extension of src/observability/reporting/retention.py or src/core/retention.py, both of which are out of scope for this subsystem per the policy doc's own Out of Scope section.

## Scope
- Build 3 new SQLite cache tables -- retrieval_index_cache (~30d), retrieval_query_cache (~7d), retrieval_packet_cache (~14d) -- as a genuinely new module, not an extension of any existing retention code.
- Implement each cache's key/value/invalidation trigger per the idea doc's Cache design table (content hash + embedding/chunking version for index cache; query+filters+corpus_generation/retrieval_version for query cache; cited-source content hashes + corpus_generation/policy version for packet cache).
- Restrict every stored row to MAY-list fields only (hashes, IDs, counts, reason codes, scores, latency, version numbers, cache-status); never store raw prompt/chunk/source text.
- Introduce the corpus_generation/retrieval_version concept (new counter or derived from knowledge_search.py's manifest.json) since this ticket is first to need it -- decide and document the source as part of scope.

## Out of Scope
- Touching src/observability/reporting/retention.py, src/core/retention.py, or any tools/agent-monitoring/*.py writer.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG) -- SQLite only.
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.
- Treating the idea doc's 30d/7d/14d durations as load-bearing values -- tests assert invalidation-trigger correctness (hash/version mismatch), not duration enforcement.

## Acceptance Criteria
- [ ] Rebuilding the embedding/index cache with unchanged content hash + embedding/chunking version returns a hit (no re-embed); changing either causes recompute and stale-row eviction.
- [ ] Query-result cache entry is rejected as stale when corpus_generation/retrieval_version changes even with identical query+filters; rejection is observable via a stale-reject/miss reason code.
- [ ] Context-packet cache entry is invalidated when any cited source's content hash no longer matches, or corpus_generation/policy version changes.
- [ ] Every stored row is inspectable and contains ONLY MAY-list fields; tested by asserting no row contains raw prompt/chunk text.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-CONTEXT-PACKET-SCHEMA

## Related Docs
- docs/observability/retrieval_retention_redaction_policy.md
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/reporting/retention.py
- src/core/retention.py
- src/engine/world_index.py
- tools/knowledge_search.py
- tests/unit/observability/test_retention_manager.py
- tests/unit/core/test_retention.py
- tests/tools/test_knowledge_search.py
- expected: tools/retrieval_cache.py
- expected: tests/tools/test_retrieval_cache.py

## Assumptions / Open Questions
- src/engine/world_index.py already defines an unrelated class literally named CacheInvalidationPolicy for simulation-tick spatial/entity/resource indexes tied to DirtySet -- must not be confused with or reused for this retrieval-cache work; new module needs distinct naming.
- The idea doc's 30d/7d/14d durations are explicitly labeled placeholders, not measured values.
- No corpus_generation/retrieval_version concept exists in code anywhere yet; whether it's a new counter or derived from knowledge_search.py's manifest.json is an open implementation decision for planning.
- Exact file path for the new cache module is not fixed by any doc -- a scoping decision for this ticket (suggested: tools/retrieval_cache.py, following tools/knowledge_search.py's precedent).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
